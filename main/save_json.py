import json
from pkg_resources import resource_string, resource_filename


def save_json():
    json_dict = {'sorting_complete': [], 'curation_complete': []}
    json_object = json.dumps(json_dict, indent=4)
    with open("sorting_record.json", "w") as outfile:
        outfile.write(json_object)


if __name__ == '__main__':
    save_json()
