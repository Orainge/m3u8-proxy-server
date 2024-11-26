# 加解密工具类

import base64
from exception import DecryptError
import server_config

# URL 加密偏移量
default_url_encrypt_offset = server_config.get_config(["security", "urlEncryptOffset", "default"], 0)
url_encrypt_offset_dict = server_config.get_config(["security", "urlEncryptOffset", "rules"], {})


def encrypt_string(original_string, server_name: str = None):
    """
    加密字符串
    :param original_string: 原始字符串
    :param server_name: 服务器名称
    """
    url_encrypt_offset = default_url_encrypt_offset

    # 根据【服务器名称】选择偏移量
    if server_name is not None and server_name in url_encrypt_offset_dict:
        url_encrypt_offset = int(url_encrypt_offset_dict[server_name])

    if url_encrypt_offset == 0:
        encoded_string = base64.urlsafe_b64encode(original_string.encode()).decode()
    else:
        encrypted_chars = [chr(ord(char) + url_encrypt_offset) for char in original_string]
        encrypted_string = ''.join(encrypted_chars)
        encoded_string = base64.urlsafe_b64encode(encrypted_string.encode()).decode()
    return encoded_string


def decrypt_string(encoded_string, server_name: str = None):
    """
    解密字符串
    :param encoded_string: 加密的字符串
    :param server_name: 服务器名称
    """
    try:
        url_encrypt_offset = default_url_encrypt_offset

        # 根据【服务器名称】选择偏移量
        if server_name is not None and server_name in url_encrypt_offset_dict:
            url_encrypt_offset = int(url_encrypt_offset_dict[server_name])

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
    encrypted = encrypt_string(test_str, "backup")
    print("Encrypted:", encrypted)

    decrypted = decrypt_string(encrypted, "backup")
    print("Decrypted:", decrypted)
