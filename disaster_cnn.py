import torch
import torch.nn as nn


class CNNEncoder(nn.Module):
    """
    Extracts spatial features from one satellite image.
    """

    def __init__(self, in_channels=3):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(256, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU()
        )

        self.pool = nn.AdaptiveAvgPool2d((1, 1))

    def forward(self, x):

        x = self.features(x)
        x = self.pool(x)

        return x.flatten(1)


class TemporalDisasterCNN(nn.Module):
    """
    Compares historical and recent satellite images.

    Input:
        historical: [B, C, H, W]
        recent:     [B, C, H, W]

    Output:
        disaster classification logits
    """

    def __init__(self, in_channels=3, num_classes=5):
        super().__init__()

        self.encoder = CNNEncoder(in_channels)

        # Each image produces 512 features.
        # We use:
        # historical features
        # recent features
        # absolute change features
        #
        # Total = 512 * 3 = 1536

        self.classifier = nn.Sequential(
            nn.Linear(1536, 512),
            nn.ReLU(),
            nn.Dropout(0.4),

            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, num_classes)
        )

    def forward(self, historical, recent):

        historical_features = self.encoder(historical)

        recent_features = self.encoder(recent)

        # Feature-level temporal change
        change_features = torch.abs(
            recent_features - historical_features
        )

        combined = torch.cat(
            [
                historical_features,
                recent_features,
                change_features
            ],
            dim=1
        )

        output = self.classifier(combined)

        return output


if __name__ == "__main__":

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Device:", device)

    model = TemporalDisasterCNN(
        in_channels=3,
        num_classes=5
    ).to(device)

    historical = torch.randn(
        2, 3, 256, 256
    ).to(device)

    recent = torch.randn(
        2, 3, 256, 256
    ).to(device)

    output = model(historical, recent)

    print("Historical:", historical.shape)
    print("Recent:", recent.shape)
    print("Output:", output.shape)

    probabilities = torch.softmax(output, dim=1)

    predictions = torch.argmax(
        probabilities,
        dim=1
    )

    print("Predictions:", predictions)
    print("Probabilities:", probabilities)