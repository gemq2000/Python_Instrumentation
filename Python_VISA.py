# visa_gpib_tool.py
import argparse
import sys
from typing import Optional
import pyvisa as visa

def open_inst(resource: str, timeout_ms: int, r_ter: Optional[str], w_ter: Optional[str]):
    rm = visa.ResourceManager()  # 可在此传入自定义VISA库路径，如 ResourceManager("C:\\Windows\\System32\\visa64.dll")
    inst = rm.open_resource(resource)
    inst.timeout = timeout_ms
    if r_ter is not None:
        inst.read_termination = r_ter
    if w_ter is not None:
        inst.write_termination = w_ter
    return rm, inst

def list_resources():
    rm = visa.ResourceManager()
    res = rm.list_resources()
    print("VISA Resources:")
    for r in res:
        print("  ", r)

def main():
    p = argparse.ArgumentParser(description="VISA GPIB helper")
    p.add_argument("--list", action="store_true", help="列出所有VISA资源然后退出")
    p.add_argument("--resource", "-r", default="GPIB0::10::INSTR", help="资源地址，如 GPIB0::10::INSTR")
    p.add_argument("--timeout", type=int, default=5000, help="超时(ms)")
    p.add_argument("--read-ter", default="\\n", help="读终止符，例如 \\n 或 空字符串'' 关闭")
    p.add_argument("--write-ter", default="\\n", help="写终止符，例如 \\n 或 空字符串'' 关闭")
    p.add_argument("--cmd", "-c", default="*IDN?", help="发送的SCPI命令（文本交互）")
    p.add_argument("--binary", action="store_true", help="使用 query_binary_values 读取二进制数据（如波形）")
    p.add_argument("--dtype", default="f", help="二进制数据类型，常见：f(32位浮点), d(64位浮点), h(16位整型)")
    p.add_argument("--big-endian", action="store_true", help="按大端解析二进制")
    p.add_argument("--raw", action="store_true", help="使用 read_raw() 读取原始字节")
    args = p.parse_args()

    if args.list:
        list_resources()
        return

    # 处理终止符
    r_ter = None if args.read_ter == "" else args.read_ter.encode("utf-8").decode("unicode_escape")
    w_ter = None if args.write_ter == "" else args.write_ter.encode("utf-8").decode("unicode_escape")

    try:
        rm, inst = open_inst(args.resource, args.timeout, r_ter, w_ter)
    except visa.VisaIOError as e:
        print("打开资源失败：", e)
        sys.exit(1)

    try:
        if args.binary:
            # 二进制查询（例如示波器波形：CURVe? / WAV:DATA?）
            # 注意：某些仪器需要先设置格式，如：WAV:FORM BYTE/WORD 或 DATa:ENC RIBinary/Little
            data = inst.query_binary_values(args.cmd, datatype=args.dtype,
                                            is_big_endian=args.big_endian, container=list)
            print(f"[BINARY] 返回 {len(data)} 点：")
            # 只预览前20个
            print(data[:20], "...") if len(data) > 20 else print(data)
        elif args.raw:
            inst.write(args.cmd)
            raw = inst.read_raw()
            print(f"[RAW] 字节数 {len(raw)}：", raw[:64], b"...")
        else:
            # 纯文本交互（最常见，如 *IDN?、MEAS:VOLT:DC? 等）
            resp = inst.query(args.cmd)
            print(resp.strip())
    except visa.VisaIOError as e:
        print("通信错误：", e)
    finally:
        try:
            inst.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
