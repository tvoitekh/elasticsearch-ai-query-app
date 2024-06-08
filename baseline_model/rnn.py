import pandas as pd
import torch
from torchtext.data.utils import get_tokenizer
from collections import Counter
from torchtext.vocab import vocab
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import re
from nltk.translate.bleu_score import corpus_bleu
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize

# Load the training data
data_path = 'training_data.csv'
df = pd.read_csv(data_path)

# Tokenize the input and output texts
tokenizer = get_tokenizer('basic_english')

# Tokenize and build vocabulary
def build_vocab(texts):
    counter = Counter()
    for text in texts:
        counter.update(tokenizer(text))
    
    # Manually specify the index for special tokens
    specials = ['<unk>', '<pad>', '<bos>', '<eos>']
    for special in specials:
        counter[special] = float('inf')  # Ensure high frequency for special tokens
    
    # Create a Vocab object
    ordered_dict = counter.most_common()
    my_vocab = vocab(Counter(dict(ordered_dict)), specials=specials)
    return my_vocab

input_texts = df['input'].tolist()
output_texts = df['output'].tolist()

input_vocab = build_vocab(input_texts)
output_vocab = build_vocab(output_texts)
input_vocab.set_default_index(input_vocab['<unk>'])
output_vocab.set_default_index(output_vocab['<unk>'])

# Encode the sequences
def encode_texts(texts, vocab, add_bos_eos=False):
    sequences = []
    for text in texts:
        tokens = tokenizer(text)
        if add_bos_eos:
            tokens = ['<bos>'] + tokens + ['<eos>']
        sequences.append([vocab[token] for token in tokens])
    return sequences

input_sequences = encode_texts(input_texts, input_vocab)
output_sequences = encode_texts(output_texts, output_vocab, add_bos_eos=True)

# Pad sequences
def pad_sequences(sequences, pad_idx):
    max_len = max(len(seq) for seq in sequences)
    padded_seqs = []
    for seq in sequences:
        padded_seq = seq + [pad_idx] * (max_len - len(seq))
        padded_seqs.append(padded_seq)
    return torch.tensor(padded_seqs)

input_pad_sequences = pad_sequences(input_sequences, input_vocab['<pad>'])
output_pad_sequences = pad_sequences(output_sequences, output_vocab['<pad>'])

# Create datasets
input_data = input_pad_sequences
output_data = output_pad_sequences[:, :-1]
target_data = output_pad_sequences[:, 1:]

# Define vocabulary sizes and padding indexes
input_vocab_size = len(input_vocab)
output_vocab_size = len(output_vocab)
pad_idx = input_vocab['<pad>']

class Seq2Seq(nn.Module):
    def __init__(self, input_vocab_size, output_vocab_size, embedding_dim, hidden_dim):
        super(Seq2Seq, self).__init__()
        self.encoder = nn.Embedding(input_vocab_size, embedding_dim)
        self.decoder = nn.Embedding(output_vocab_size, embedding_dim)
        self.enc_lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.dec_lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_vocab_size)
    
    def forward(self, src, trg, teacher_forcing_ratio=0.5):
        # Encoder
        embedded = self.encoder(src)
        enc_outputs, (hidden, cell) = self.enc_lstm(embedded)
        
        # Decoder
        dec_inputs = trg
        dec_inputs_embedded = self.decoder(dec_inputs)
        dec_outputs, _ = self.dec_lstm(dec_inputs_embedded, (hidden, cell))
        outputs = self.fc(dec_outputs)
        return outputs

# Define the model parameters
embedding_dim = 256
hidden_dim = 512

# Instantiate the model
model = Seq2Seq(input_vocab_size, output_vocab_size, embedding_dim, hidden_dim)

# Create dataloaders
dataset = TensorDataset(input_data, output_data, target_data)
dataloader = DataLoader(dataset, batch_size=64, shuffle=True)

# Define optimizer and loss function
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss(ignore_index=pad_idx)

# Training loop
def train(model, dataloader, optimizer, criterion, num_epochs=30):
    model.train()
    for epoch in range(num_epochs):
        epoch_loss = 0
        for src, trg, tgt in dataloader:
            optimizer.zero_grad()
            output = model(src, trg)
            output_dim = output.shape[-1]
            output = output.view(-1, output_dim)
            tgt = tgt.view(-1)
            loss = criterion(output, tgt)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        print(f'Epoch {epoch + 1}, Loss: {epoch_loss / len(dataloader)}')

train(model, dataloader, optimizer, criterion)

# Define function for inference
def generate(model, input_seq, max_length=50):
    model.eval()
    with torch.no_grad():
        embedded = model.encoder(input_seq)
        enc_outputs, (hidden, cell) = model.enc_lstm(embedded)
        
        dec_input = torch.tensor([[output_vocab['<bos>']]], device=input_seq.device)
        generated_tokens = []
        
        for _ in range(max_length):
            dec_input_embedded = model.decoder(dec_input)
            dec_output, (hidden, cell) = model.dec_lstm(dec_input_embedded, (hidden, cell))
            dec_output = model.fc(dec_output[:, -1, :])
            pred_token = dec_output.argmax(1).item()
            generated_tokens.append(pred_token)
            if pred_token == output_vocab['<eos>']:
                break
            dec_input = torch.tensor([[pred_token]], device=input_seq.device)

        # Modify this line to use get_itos() if 'itos' attribute is not present
        idx_to_token = output_vocab.get_itos() if hasattr(output_vocab, 'get_itos') else output_vocab.itos
        return ' '.join([idx_to_token[idx] for idx in generated_tokens if idx not in {output_vocab['<bos>'], output_vocab['<eos>'], output_vocab['<pad>']}])


def test_model_with_bleu(model, data_path, input_vocab, output_vocab, device='cpu'):
    """
    Load test data, generate predictions using the model, and calculate BLEU score.
    """
    # Load test data
    test_df = pd.read_csv(data_path)
    
    # Ensure all output data is treated as string and handle missing data
    test_df['output'] = test_df['output'].fillna('')  # Replace NaN with empty string
    test_df['output'] = test_df['output'].apply(str)  # Ensure all data is treated as string

    test_inputs = test_df['input'].tolist()
    test_references = [word_tokenize(ref.lower()) for ref in test_df['output'].tolist()]

    # Prepare model for inference
    model.eval()
    model.to(device)
    predictions = []

    # Tokenize and encode the input for the model
    for sentence in test_inputs:
        tokens = [input_vocab[token] for token in tokenizer(sentence)]
        tokens_tensor = torch.tensor([tokens], dtype=torch.long, device=device)
        # Generate model output
        generated_text = generate(model, tokens_tensor)
        predictions.append(word_tokenize(generated_text.lower()))

    # Calculate BLEU score
    bleu_score = corpus_bleu([[ref] for ref in test_references], predictions)
    return bleu_score


data_path = 'test_data.csv'  # Update this path to your actual test data CSV file
bleu_score = test_model_with_bleu(model, data_path, input_vocab, output_vocab)
print("BLEU Score:", bleu_score)
