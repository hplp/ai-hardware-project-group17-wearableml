import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import glob

# Function to load and process data
def load_data(filenames, feature_cols, label_col):
    X_list, y_list = [], []
    for file in filenames:
        data = np.loadtxt(file, delimiter=',', skiprows=1)
        X_list.append(data[:, feature_cols])
        y_list.append(data[:, label_col])
    X = np.vstack(X_list)
    y = np.hstack(y_list)
    return X, y

# Load training data from multiple subjects
train_files = [f"Subject {i}.csv" for i in range(1, 6)]
X_train, y_train = load_data(train_files, feature_cols=range(4), label_col=4)

# Load testing data from multiple subjects
test_files = [f"Subject {i}.csv" for i in range(6, 8)]
X_test, y_test = load_data(test_files, feature_cols=range(4), label_col=4)

# Convert to PyTorch tensors
X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)

# Calculate mean and standard deviation on training data
mean = X_train.mean(dim=0)
std = X_train.std(dim=0)

# Normalize the data
X_train_norm = (X_train - mean) / std
X_test_norm = (X_test - mean) / std

# Define the model
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(4, 4)
        self.fc2 = nn.Linear(4, 1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)  # No activation here
        return x

model = Net()

# Define loss and optimizer
criterion = nn.BCEWithLogitsLoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Training loop
num_epochs = 1000
for epoch in range(num_epochs):
    optimizer.zero_grad()
    outputs = model(X_train_norm)
    loss = criterion(outputs, y_train)
    loss.backward()
    optimizer.step()

    # Calculate accuracy every 100 epochs
    if (epoch + 1) % 100 == 0:
        with torch.no_grad():
            predicted = torch.sigmoid(model(X_test_norm))
            predicted = (predicted > 0.5).float()
            accuracy = (predicted.eq(y_test).sum() / y_test.shape[0]).item() * 100
        print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}, Accuracy: {accuracy:.2f}%')

# Save the model parameters
weights = {
    'fc1_weight': model.fc1.weight.detach().numpy(),
    'fc1_bias': model.fc1.bias.detach().numpy(),
    'fc2_weight': model.fc2.weight.detach().numpy(),
    'fc2_bias': model.fc2.bias.detach().numpy()
}

np.savez('model_weights.npz', **weights)

# Save mean and std for normalization on Arduino
np.savez('data_normalization.npz', mean=mean.numpy(), std=std.numpy())

print("Training complete. Model parameters and normalization parameters have been saved.")

"""
Epoch [100/1000], Loss: 0.5340, Accuracy: 96.50%
Epoch [200/1000], Loss: 0.3953, Accuracy: 99.70%
Epoch [300/1000], Loss: 0.2763, Accuracy: 99.65%
Epoch [400/1000], Loss: 0.1947, Accuracy: 99.60%
Epoch [500/1000], Loss: 0.1422, Accuracy: 99.60%
Epoch [600/1000], Loss: 0.1084, Accuracy: 99.60%
Epoch [700/1000], Loss: 0.0858, Accuracy: 99.70%
Epoch [800/1000], Loss: 0.0703, Accuracy: 99.70%
Epoch [900/1000], Loss: 0.0592, Accuracy: 99.70%
Epoch [1000/1000], Loss: 0.0509, Accuracy: 99.70%
Training complete. Model parameters and normalization parameters have been saved.
Model parameters and normalization parameters have been converted to C arrays and saved in 'model_parameters.h'.
"""

# Convert parameters to C format for deployment
def array_to_c(name, array):
    if len(array.shape) == 2:
        rows, cols = array.shape
        c_str = f'float {name}[{rows}][{cols}] = {{\n'
        for i in range(rows):
            c_str += '  {' + ', '.join(f'{x:.6f}f' for x in array[i]) + '}'
            if i != rows - 1:
                c_str += ',\n'
        c_str += '\n};\n'
    elif len(array.shape) == 1:
        c_str = f'float {name}[{len(array)}] = {{' + ', '.join(f'{x:.6f}f' for x in array) + '}};\n'
    else:
        raise ValueError("Array has more than 2 dimensions")
    return c_str

# Generate C arrays and save to 'model_parameters.h'
with open('model_parameters.h', 'w') as f:
    f.write('// Model Weights and Biases\n')
    f.write(array_to_c('fc1_weight', weights['fc1_weight']))
    f.write(array_to_c('fc1_bias', weights['fc1_bias']))
    f.write(array_to_c('fc2_weight', weights['fc2_weight'].flatten()))
    f.write(f'float fc2_bias = {weights["fc2_bias"][0]:.6f}f;\n\n')

    f.write('// Normalization Parameters\n')
    f.write(array_to_c('mean', mean.numpy()))
    f.write(array_to_c('std_dev', std.numpy()))

print("Model parameters and normalization parameters have been converted to C arrays and saved in 'model_parameters.h'.")

"""
Model parameters and normalization parameters have been converted to C arrays and saved in 'model_parameters.h'.
"""