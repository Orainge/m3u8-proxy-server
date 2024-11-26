# 加解密工具类

import base64
from exception import DecryptError
import server_config

# URL 加密偏移量
url_encrypt_offset = server_config.get_config(["security", "urlEncryptOffset"], 0)


def encrypt_string(original_string):
    """
    加密字符串
    :param original_string: 原始字符串
    """
    if url_encrypt_offset == 0:
        encoded_string = base64.urlsafe_b64encode(original_string.encode()).decode()
    else:
        encrypted_chars = [chr(ord(char) + url_encrypt_offset) for char in original_string]
        encrypted_string = ''.join(encrypted_chars)
        encoded_string = base64.urlsafe_b64encode(encrypted_string.encode()).decode()
    return encoded_string


def decrypt_string(encoded_string):
    """
    解密字符串
    :param encoded_string: 加密的字符串
    """
    try:
        if url_encrypt_offset == 0:
            decoded_string = base64.urlsafe_b64decode(encoded_string.encode()).decode()
        else:
            decoded_string = base64.urlsafe_b64decode(encoded_string.encode()).decode()
            decrypted_chars = [chr(ord(char) - url_encrypt_offset) for char in decoded_string]
            decoded_string = ''.join(decrypted_chars)
        return decoded_string
    except Exception:
        raise DecryptError()


if __name__ == '__main__':
    # 示例用法
    test_str = "Hello, world!"
    encrypted = encrypt_string(test_str)
    print("Encrypted:", encrypted)

    decrypted = decrypt_string(encrypted)
    print("Decrypted:", decrypted)
