import pyvisa as visa

rm = visa.ResourceManager()  # 如果你安装了NI/Keysight VISA，会自动找到库
inst = rm.open_resource("GPIB0::10::INSTR", read_termination="\n", write_termination="\n", timeout=5000)
print(inst.query("*IDN?"))
