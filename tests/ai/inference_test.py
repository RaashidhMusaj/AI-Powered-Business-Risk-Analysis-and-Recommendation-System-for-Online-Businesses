from core.ai.inference.inference_engine import InferenceEngine
from core.ai.inference.model_loader import ModelLoader

def main():
    loader = ModelLoader.get_instance()
    engine = InferenceEngine(loader)

    outputs = engine.predict(
        "Delivery was very late but product quality is excellent."
    )

    print(outputs.keys())
    print(outputs["sentiment_logits"].shape)
    print(outputs["aspect_logits"].shape)


if __name__ == "__main__":
    main()