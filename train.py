from dataloader import TransformerOilTempDataset
from torch.utils.data import DataLoader
from model import *
import torch.nn as nn
import os

if __name__ == '__main__':
    device = torch.device('cuda')

    if not os.path.exists("result_picture"):
        os.makedirs("result_picture")

    if not os.path.exists("best_model"):
        os.makedirs("best_model")


    def parse_args():
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--model", "-m", default='Base', help="which model")
        args = parser.parse_args()
        return args


    args = parse_args()

    train_data = TransformerOilTempDataset('Dataset/ETT-small/ETTm1.csv', 10, is_test=False)
    test_data = TransformerOilTempDataset('Dataset/ETT-small/ETTm1.csv', 10, is_test=True)
    print_step = 10

    train_loader = DataLoader(train_data, batch_size=256, shuffle=True, num_workers=4)
    test_loader = DataLoader(test_data, batch_size=256, shuffle=True, num_workers=4)

    model_dict = {
        "Base": CNNLSTMModel,
        "SE": CNNLSTMModel_SE,
        "ECA": CNNLSTMModel_ECA,
        "CBAM": CNNLSTMModel_CBAM,
        "HW": CNNLSTMModel_HW
    }

    model = model_dict[args.model]()
    model = model.to(device)

    print(model)
    print(f"training model is {args.model}")
    criterion = nn.MSELoss()
    criterion = criterion.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    min_loss = 99999
    for epoch in range(100):
        print(f'epoch:{epoch}')
        running_loss = 0.0
        for step, (data, label) in enumerate(train_loader):
            data = data.to(device)
            label = label.to(device)
            out = model(data)
            loss = criterion(out, label)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            if step % print_step == 0:  # 每500个batch打印一次训练状态
                with torch.no_grad():
                    mse_loss = 0.0
                    for data, label in test_loader:
                        data = data.to(device)
                        label = label.to(device)
                        out = model(data)
                        loss = criterion(out, label)
                        mse_loss += loss.item()
                    if mse_loss / len(test_loader) < min_loss:
                        torch.save(model.state_dict(), f"best_model/{args.model}_best.pth")
                        print("save_best")
                        min_loss = mse_loss / len(test_loader)
                    print(f"step:{step}, test loss:{mse_loss / len(test_loader)}")

    print("done")
