import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pathlib import Path
import shutil
import os
from cerberus import Validator

FILES_VOLUME = "/usr/share/logstash/files"
DLQ_VOLUME = "/usr/share/logstash/dlq"
PIPELINES_VOLUME = FILES_VOLUME + "/generated/"
PIPELINES_VOLUME_MAIN = PIPELINES_VOLUME + "main/"
PIPELINES_VOLUME_DLQ = PIPELINES_VOLUME + "dlq/"

JAVA_TRUSTSTORE_PATH = FILES_VOLUME + "/java.truststore"

GENERATED_PATH = Path("./generated")
GENERATED_MAIN_PATH = GENERATED_PATH.joinpath("main")
GENERATED_DLQ_PATH = GENERATED_PATH.joinpath("dlq")
TEMPLATES_PATH = Path("./templates")

VALUES_SCHEMA = schema = {
    'kafka_hosts': {
        'type': 'list',
        'schema': {'type': 'string'},
        'required': True
    },
    'kafka_group_id': {'type': 'string', 'required': True},
    'logstash_pipelines': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'name': {'type': 'string', 'required': True,'regex': r'^[a-zA-Z0-9.]+$'},
                'topics_pattern': {'type': 'string', 'required': True},
                'output': {'type': 'string', 'required': False},
                'input': {'type': 'string', 'required': False},
                'document_id': {'type': 'string', 'required': False},
                'datastream': {'type': 'boolean', 'required': False},
                'filters': {
                    'type': 'list',
                    'schema': {'type': 'string'},
                    'required': False
                }
            },
        },
        'required': True
    }
}

validator = Validator(schema)

yaml_path = f"values_{os.getenv("ENV")}.yml"

if not os.path.isfile(yaml_path):
    raise ValueError(
        f"{yaml_path} does not exist or is not a file"
    )

with open(yaml_path, "r") as file:
    values = yaml.safe_load(file)

if not validator.validate(values):
    raise ValueError(f"values are invalid according to the schema {validator.errors}")

if GENERATED_PATH.is_dir():
    shutil.rmtree(GENERATED_PATH)

GENERATED_MAIN_PATH.mkdir(parents=True, exist_ok=True)
GENERATED_DLQ_PATH.mkdir(parents=True, exist_ok=True)

jinja2_loader = FileSystemLoader(searchpath=TEMPLATES_PATH)
jinja2 = Environment(
    loader=jinja2_loader, undefined=StrictUndefined
)

print(f"GENERATING PIPELINES")

logstash_pipelines = values["logstash_pipelines"]

default_filters = ["gef_ecs"]
default_output_datastream = "elk_datastream"
default_output_index = "elk_index"
default_input = "kafka"

secret_pipelines = []

for item in logstash_pipelines:
    
    item_name = item["name"]
    is_datastream = item.get("datastream", True)
    print(f"START - {item_name}")
    has_dlq = "skip_dlq" not in item or not item["skip_dlq"]
    print(f"has_dlq: {has_dlq}")
    filters = item.get("filters", default_filters)
    print(f"filters: {filters}")
    default_output = default_output_datastream if is_datastream else default_output_index
    output = f"outputs/{item.get("output", default_output)}.cfg.j2"
    print(f"output: {output}")
    input = f"inputs/{item.get("input", default_input)}.cfg.j2" 
    print(f"input: {input}")
    document_id = item.get("document_id", "%{[@metadata][_id]}")
    print(f"document_id: {document_id}")

    pipeline_id = f"{item_name}-main"
    pipeline_file = f"{pipeline_id}.cfg.j2"

    template_params = {
        "item": item,
        "values": values,
        "item_name": item_name,
        "document_id": document_id,
        "pipeline_id": pipeline_id,
        "java_truststore_path": JAVA_TRUSTSTORE_PATH,
        "logstash_dlq_path": DLQ_VOLUME,
    }

    input_content = jinja2.get_template(input).render(**template_params)

    filters_content = [jinja2.get_template(f"filters/{filter}.cfg.j2").render(**template_params) for filter in filters]

    output_content = jinja2.get_template(output).render(**template_params)

    with open(GENERATED_MAIN_PATH / pipeline_file, "w") as output_file:
        output_file.write(input_content)
        output_file.write(os.linesep)
        output_file.write(os.linesep.join(filters_content))
        output_file.write(os.linesep)
        output_file.write(output_content)

    pipeline_dict = {
        "pipeline.id": pipeline_id,
        "path.config": f"{PIPELINES_VOLUME_MAIN}{pipeline_file}",
        "dead_letter_queue.enable": has_dlq
    }

    if has_dlq:
        pipeline_dict["path.dead_letter_queue"] = DLQ_VOLUME

    secret_pipelines.append(pipeline_dict)

    if has_dlq:
        dlq_params = {**template_params, 'dataset': 'dlq'}

        dlq_content = jinja2.get_template("inputs/dlq.cfg.j2").render(
            **dlq_params
        )

        filter_content = jinja2.get_template("filters/dlq.cfg.j2").render(**dlq_params)
        output_content = jinja2.get_template("outputs/elk_datastream.cfg.j2").render(**dlq_params)

        pipeline_id_dlq = f"{item_name}-dlq"
        pipeline_file_dlq = f"{pipeline_id_dlq}.cfg.j2"

        with open(GENERATED_DLQ_PATH / pipeline_file_dlq, "w") as output_file:
            output_file.write(dlq_content)
            output_file.write(os.linesep)
            output_file.write(filter_content)
            output_file.write(os.linesep)
            output_file.write(output_content)

        secret_pipelines.append(
            {
                "pipeline.id": pipeline_id_dlq,
                "path.config": f"{PIPELINES_VOLUME_DLQ}{pipeline_file_dlq}",
                "dead_letter_queue.enable": False,
            }
        )

    print(f"DONE - {item_name}")


def str_presenter(dumper, data):
    if data.count("\n") > 0:
        data = "\n".join(
            [line.rstrip() for line in data.splitlines()]
        )  # Remove any trailing spaces, then put it back together again
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)

secret_string = yaml.dump(
    {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": "logstash-pipeline"},
        "stringData": {
            "pipelines.yml": yaml.dump(
                secret_pipelines, default_flow_style=False, sort_keys=False
            )
        },
    },
    default_flow_style=False,
    sort_keys=False,
)

with open(GENERATED_PATH / "secret.yml", "w") as output_file:
    output_file.write("# DO NOT EDIT THIS FILE MANUALLY")
    output_file.write(os.linesep)
    output_file.write(secret_string)

print(f"END")
