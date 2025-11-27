from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer

import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)


def run_server():
    # Holding registers:
    # 40001: PT_101 value * 10 (e.g., 750.0 psi -> 7500)
    # 40002: FT_201 value * 10
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [7500, 2000])
    )
    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "Demo"
    identity.ProductCode = "MD"
    identity.VendorUrl = "http://example.com"
    identity.ProductName = "SCADA Demo Modbus Server"
    identity.ModelName = "Modbus Server"
    identity.MajorMinorRevision = "1.0"

    # Listen on localhost:5020
    StartTcpServer(context, identity=identity, address=("127.0.0.1", 5020))


if __name__ == "__main__":
    run_server()
