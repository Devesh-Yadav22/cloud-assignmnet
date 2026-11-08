"""Loads the student model from object storage and runs inference (Task 3).

Model weights are not baked into the image; MODEL_URI identifies the model files.
"""
import json
import os
import tempfile

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.json")
with open(SCHEMA_PATH, encoding="utf-8") as schema_file:
    _SCHEMA = json.load(schema_file)
KEYS = set(_SCHEMA["keys"])
INTENTS = set(_SCHEMA["intents"])


def extract_json(generated):
    """Extract the first complete JSON object from generated text."""
    text = generated.strip()
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return text[start:]


def validate(raw):
    """Return the parsed object when it conforms exactly to schema.json, otherwise None."""
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(obj, dict) or set(obj) != KEYS:
        return None
    if not isinstance(obj.get("intent"), str) or obj["intent"] not in INTENTS:
        return None
    for key in ("date", "time", "place"):
        if obj[key] is not None and not isinstance(obj[key], str):
            return None
    return obj


def _resolve_model_dir(model_uri):
    """Resolve an S3 URI or local model directory to a local directory."""
    if model_uri.startswith("s3://"):
        return _download_model(model_uri)
    if model_uri.startswith("file://"):
        model_uri = model_uri[len("file://"):]
    if not os.path.isdir(model_uri):
        raise RuntimeError(f"MODEL_URI local path not found: {model_uri}")
    return model_uri


def _download_model(model_uri):
    assert model_uri.startswith("s3://"), "MODEL_URI must be s3://<bucket>/<prefix>"
    bucket, _, prefix = model_uri[len("s3://"):].partition("/")
    prefix = prefix.rstrip("/") + "/"
    import boto3
    from botocore.client import Config
    s3 = boto3.client(
        "s3", endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    destination = tempfile.mkdtemp(prefix="model-")
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    objects = response.get("Contents", [])
    if not objects:
        raise RuntimeError(f"no objects under {model_uri}")
    for item in objects:
        name = item["Key"][len(prefix):]
        if name:
            path = os.path.join(destination, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            s3.download_file(bucket, item["Key"], path)
    return destination


class Runner:
    def __init__(self):
        self.ready = False
        self.model = None
        self.tokenizer = None
        self.max_new_tokens = int(os.environ.get("MAX_NEW_TOKENS", "64"))

    def load(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        local_dir = _resolve_model_dir(os.environ["MODEL_URI"])
        self.tokenizer = AutoTokenizer.from_pretrained(local_dir)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(local_dir)
        self.model.eval()
        self.ready = True

    def raw_output(self, text):
        """Generate and return candidate JSON for a command."""
        import torch
        prompt = f"Command: {text}\nJSON:"
        encoded = self.tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            generated = self.model.generate(
                **encoded, max_new_tokens=self.max_new_tokens, do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        new_tokens = generated[0][encoded["input_ids"].shape[1]:]
        decoded = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        return extract_json(decoded)
