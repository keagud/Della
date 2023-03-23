from pathlib import Path
from typing import Any, Optional

import fabric
import toml


def load_config(
    location: str = "~/.config/della/config.toml",
) -> Optional[dict[str, Any]]:
    config_path = Path(location).expanduser().resolve()

    with open(config_path, "r") as config_file:
        config_dict = toml.load(config_file)

    return config_dict.get("remote")


def main():
    config = load_config()

    if config is None:
        raise ValueError

    private_key_location = Path(config["private_key_location"]).expanduser().resolve()

    connect_args = {
        "host": config["ip"],
        "user": config["user"],
        "connect_kwargs": {"key_filename": private_key_location.as_posix()},
    }

    with fabric.Connection(**connect_args) as c:
        result = c.run("whoami")
        print(result)


if __name__ == "__main__":
    main()
