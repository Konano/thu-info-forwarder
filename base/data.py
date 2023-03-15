import json
import traceback

from base.log import logger


class _localStore:
    """
    A local file store.
    """

    def __init__(self, filepath: str, default: dict) -> None:
        self.filepath = filepath
        self.default = default
        self.load()

    def load(self) -> None:
        """
        Load data from file.
        """
        try:
            with open(self.filepath, 'r') as f:
                self.data = json.load(f)
        except Exception as e:
            logger.warning(
                f'Failed to load data, use default. {self.filepath}, {e}')
            logger.debug(traceback.format_exc())
            self.data = self.default
            with open(self.filepath, 'w') as f:
                json.dump(self.data, f)

    def __dump_check(self, format=True) -> bool:
        """
        Check if the data can be dumped.
        :param format: format json
        :return: True if the data can be dumped, False otherwise
        """
        try:
            if format:  # format json
                json.dumps(self.data,
                           ensure_ascii=False, sort_keys=True, indent=4, default=str)
            else:
                json.dumps(self.data, default=str)
            return True
        except Exception as e:
            logger.warning(f'Failed to dump data. {self.filepath}, {e}')
            logger.debug(traceback.format_exc())
            return False

    def dump(self, format=True) -> None:
        """
        Dump data to file.
        :param format: format json
        """
        if not self.__dump_check(format):  # check if the data can be dumped
            return
        try:
            with open(self.filepath, 'w') as f:
                if format:
                    json.dump(self.data, f,
                              ensure_ascii=False, sort_keys=True, indent=4, default=str)
                else:
                    json.dump(self.data, f, default=str)
        except Exception as e:
            logger.error(f'Failed to dump data to file. {self.filepath}, {e}')
            logger.debug(traceback.format_exc())

    def update(self, value: dict, update=True) -> None:
        self.data = value
        update and self.dump()

    def __iter__(self):
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def clear(self, update=True) -> None:
        self.data.clear()
        update and self.dump()


class localDict(_localStore):
    def __init__(self, name: str, default: dict = None, folder='data') -> None:
        if default is None:
            default = {}
        filepath = folder + '/' + name + '.json'
        super().__init__(filepath, default)

    def __getitem__(self, key: str) -> object:
        return self.data.get(key, None)

    def __setitem__(self, key: str, value: object) -> None:
        self.data[key] = value

    def __delitem__(self, key: str) -> None:
        del self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def keys(self) -> list:
        return self.data.keys()

    def values(self) -> list:
        return self.data.values()

    def get(self, key: str) -> object:
        return self.data.get(key)

    def items(self) -> list:
        return self.data.items()

    def set(self, key: str, value: object, update=True) -> None:
        self.data[key] = value
        update and self.dump()

    def delete(self, key: str, update=True) -> None:
        del self.data[key]
        update and self.dump()
