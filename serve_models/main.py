import os
from typing import Union
from functools import lru_cache

from fastapi import FastAPI, status, Response
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer


@app.get("/")
async def index():
    model_shortname = os.environ["MODEL_NAME"]
    return {
        "message": f"Hello! This is a server for {model_shortname}. "
                   "Go to /generate/ for generation requests."
    }


@lru_cache(maxsize=None)
def get_model_and_tokenizer():

    model_shortname = os.environ["MODEL_NAME"]

    valid_model_shortnames = ["gptj", "opt", "neox20b", "t0pp"]
    assert model_shortname in valid_model_shortnames, \
        f"Model name {model_shortname} not in {valid_model_shortnames}"

    if model_shortname == "gptj":

        model_name = "EleutherAI/gpt-j-6B"
        model = AutoModelForCausalLM.from_pretrained(
            model_name, revision="sharded", device_map="auto", # torch_dtype=torch.float16
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    elif model_shortname == "opt":

        model_name = "facebook/opt-66b"
        model = AutoModelForCausalLM.from_pretrained(
            model_name, revision="main", device_map="auto", torch_dtype=torch.float16
        ).cuda()
        # the fast tokenizer currently does not work correctly
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)

    elif model_shortname == "neox20b":

        model_name = "EleutherAI/gpt-neox-20b"
        model = AutoModelForCausalLM.from_pretrained(
            model_name, revision="main", device_map="auto", # torch_dtype=torch.float16
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    elif model_shortname == "t0pp":

        model_name = "bigscience/T0pp"
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name, revision="sharded", device_map="auto", # torch_dtype=torch.bfloat16
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    return model, tokenizer


app = FastAPI()


@app.get("/generate/")
async def generate(
        prompt: str,
        max_input: int = None,
        max_length: int = 20,
        min_length: int = 10,
        do_sample: bool = False,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 1.0,
        num_return_sequences: int = 1,
        return_dict_in_generate: bool = False,
    ):

        model, tokenizer = get_model_and_tokenizer()

        inputs = tokenizer.encode(
            prompt,
            return_tensors="pt",
            max_length=max_input
        )
        generated_ids = model.generate(
            inputs,
            max_input=max_input,
            max_length=max_length,
            min_length=min_length,
            do_sample=do_sample,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            num_return_sequences=num_return_sequences,
            return_dict_in_generate=return_dict_in_generate,
        )

        generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        return {"generated_text": generated_text}

# get_model_and_tokenizer() # To force load the model.