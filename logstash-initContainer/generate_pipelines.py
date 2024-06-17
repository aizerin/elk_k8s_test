import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pathlib import Path
import shutil
import os

yaml_path = f"values_{os.getenv("ENV")}.yml"

if not os.path.isfile(yaml_path):
    raise ValueError(
        f"{yaml_path} does not exist or is not a file"
    )

files_volume = "/usr/share/logstash/files"
dlq_volume = "/usr/share/logstash/dlq"
pipelines_volume = files_volume + "/generated/"
java_truststore_path = files_volume + "/java.truststore"
java_truststore_password = "changeit"


generated_path = Path("./generated")
templates_path = Path("./templates")

if generated_path.is_dir():
    shutil.rmtree(generated_path)

print(f"GENERATE OUTPUTS")

templates_output_path = templates_path.joinpath("outputs")
generated_output_path = generated_path.joinpath("outputs")


template_output_loader = FileSystemLoader(searchpath=templates_output_path)
template_output_env = Environment(
    loader=template_output_loader, undefined=StrictUndefined
)

generated_output_path.mkdir(parents=True, exist_ok=True)

for file_path in templates_output_path.iterdir():
    if file_path.is_file() and file_path.name != "macros.j2":
        print(f"processing: {file_path}")
        template = template_output_env.get_template(file_path.name)
        content = template.render()
        output_file_path = generated_output_path / file_path.name.replace(".j2", "")
        with open(output_file_path, "w") as output_file:
            output_file.write(content)
        print(f"DONE processing: {file_path}")

print(f"END GENERATE OUTPUTS")

print(f"GENERATE FILTERS")

# pro filtry nemame j2 templaty, takze se to jen presune
# je to tu spis pro konzistentni chovani aby tento script pripravil soubory
# a potencialne do budoucna kdybychom chteli mit neco s j2

templates_filters_path = templates_path.joinpath("filters")
generated_filters_path = generated_path.joinpath("filters")

generated_filters_path.mkdir(parents=True, exist_ok=True)

for file_path in templates_filters_path.iterdir():
    if file_path.is_file():
        print(f"processing: {file_path}")
        output_file_path = generated_filters_path / file_path.name
        shutil.copy2(file_path, output_file_path)
        print(f"DONE processing: {file_path}")

print(f"END GENERATE FILTERS")

print(f"GENERATE INPUTS")

with open(yaml_path, "r") as file:
    data = yaml.safe_load(file)

logstash_pipelines = data["logstash_pipelines"]

default_filters = "filters/02_filter_gef_ecs"
default_output_datastream = "outputs/01_output_elk_datastream"
default_output_index = "outputs/01_output_elk_index"
default_input = "kafka_input"

templates_input_path = templates_path.joinpath("inputs")
generated_input_path = generated_path.joinpath("inputs")

template_input_loader = FileSystemLoader(searchpath=templates_input_path)
template_input_env = Environment(
    loader=template_input_loader, undefined=StrictUndefined
)

generated_input_path.mkdir(parents=True, exist_ok=True)

pipelines = []

for item in logstash_pipelines:
    item_name = item["datastream_name"] if "datastream_name" in item else item["index_name"]
    is_datastream = "datastream_name" in item
    print(f"processing: {item_name}")
    has_dlq = "skip_dlq" not in item or not item["skip_dlq"]
    if "skip_kafka" not in item or not item["skip_kafka"]:
        filters = item.get("filter", default_filters)
        print(f"filters: {filters}")
        output = item.get("output", default_output_datastream if is_datastream else default_output_index)
        print(f"output: {output}")
        input = item.get("input", default_input) + ".cfg.j2"
        print(f"input: {input}")

        template = template_input_env.get_template(input)

        content = template.render(
            item=item,
            item_name=item_name,
            java_truststore_path=java_truststore_path,
            java_truststore_password=java_truststore_password,
            kafka_hosts=data["kafka_hosts"],
            kafka_group_id=data["kafka_group_id"],
        )
        pipeline_id = f"01_input_{item_name}"

        with open(generated_input_path / f"{pipeline_id}.cfg", "w") as output_file:
            output_file.write(content)

        pipelines.append(
            {
                "pipeline.id": pipeline_id,
                "path.config": f"{pipelines_volume}{{inputs/{pipeline_id},{filters},{output}}}.cfg",
                "dead_letter_queue.enable": has_dlq,
                "path.dead_letter_queue": dlq_volume,
            }
        )
        print(f"DONE processing: {item_name}")
    else:
        print(f"skipping input: {item_name}")
    if has_dlq:

        template = template_input_env.get_template("dlq_input.cfg.j2")

        content = template.render(
            item=item,
            item_name=item_name,
            logstash_dlq_path=dlq_volume,
        )

        pipeline_id = f"01_input_{item_name}-dlq"

        with open(generated_input_path / f"{pipeline_id}.cfg", "w") as output_file:
            output_file.write(content)

        pipelines.append(
            {
                "pipeline.id": pipeline_id,
                "path.config": f"{pipelines_volume}{{inputs/{pipeline_id},filters/01_filter_dlq,01_output_elk}}.cfg",
                "dead_letter_queue.enable": False,
            }
        )
        print(f"DONE processing: {item_name}")
    else:
        print(f"skipping dlq: {item_name}")


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
                pipelines, default_flow_style=False, sort_keys=False
            )
        },
    },
    default_flow_style=False,
    sort_keys=False,
)

with open(generated_path / "secret.yml", "w") as output_file:
    output_file.write(secret_string)

print(f"END GENERATE INPUTS")
