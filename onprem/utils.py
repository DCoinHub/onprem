# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_utils.ipynb.

# %% auto 0
__all__ = ['download', 'get_datadir', 'split_list']

# %% ../nbs/02_utils.ipynb 3
import os.path
import requests
import sys
def download(url, filename, verify=False):
    with open(filename, "wb") as f:
        response = requests.get(url, stream=True, verify=verify)
        total = response.headers.get("content-length")

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            # print(total)
            for data in response.iter_content(
                chunk_size=max(int(total / 1000), 1024 * 1024)
            ):
                downloaded += len(data)
                f.write(data)
                done = int(50 * downloaded / total)
                sys.stdout.write("\r[{}{}]".format("█" * done, "." * (50 - done)))
                sys.stdout.flush()


def get_datadir():
    home = os.path.expanduser("~")
    datadir = os.path.join(home, "onprem_data")
    if not os.path.isdir(datadir):
        os.mkdir(datadir)
    return datadir


def split_list(input_list, chunk_size):
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i:i + chunk_size]
