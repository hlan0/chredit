import numpy as np


class FileIO:
    """
    Class for reading and writing files.
    """
    def __init__(self) -> None:
        pass

    def read_file(self, file_path: str) -> np.ndarray:
        """
        Read a file and return the binary data.
        """
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()

            byte_str = ''
            for byte in raw_data:
                byte_str += bin(byte)[2:].zfill(8)
            byte_list = list(byte_str)

            patterns = []
            for i in range(0, len(byte_list), 128):
                map1 = []
                for j in range(0, 64, 8):
                    row = byte_list[i+j:i+j+8]
                    map1.append(row)

                map2 = []
                for j in range(64, 128, 8):
                    row = byte_list[i+j:i+j+8]
                    map2.append(row)

                map3 = np.char.add(map1, map2)
                color_map = {'00': 0, '10': 1, '01': 2, '11': 3}
                map3 = np.vectorize(color_map.get)(map3)

                patterns.append(map3)

            table_a = patterns[:256]
            table_a_display = np.zeros((128, 128), dtype=int)

            table_b = patterns[256:]
            table_b_display = np.zeros((128, 128), dtype=int)

            cur_idx = 0

            for i in range(0, 128, 8):
                for j in range(0, 128, 8):
                    table_a_display[i:i+8, j:j+8] = table_a[cur_idx]
                    table_b_display[i:i+8, j:j+8] = table_b[cur_idx]
                    cur_idx += 1

            return table_a_display, table_b_display
        except Exception as e:
            print(f'Error reading file: {e}')
            return np.zeros((128, 128), dtype=int), np.zeros((128, 128), dtype=int)

    def to_binary(self, x: np.ndarray) -> str:
        """
        Convert a numpy array to CHR binary.
        """
        bin_data = []

        for i in range(0, 128, 8):
            for j in range(0, 128, 8):
                block = x[i:i+8, j:j+8]
                bin_data.append(block)

        inverse_color_map = {0: '00', 1: '10', 2: '01', 3: '11'}
        bin_data = np.vectorize(inverse_color_map.get)(bin_data)

        map1 = np.vectorize(lambda x: x[:1])(bin_data)
        map2 = np.vectorize(lambda x: x[1:])(bin_data)

        res = ''
        for i in range(256):
            res += ''.join(map1[i].flatten()) + ''.join(map2[i].flatten())

        return res
