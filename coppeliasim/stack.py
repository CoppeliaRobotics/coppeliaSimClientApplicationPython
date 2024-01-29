import ctypes


def read_null(stackHandle):
    from coppeliasim.lib import (
        simGetStackItemType,
        simPopStackItem,
        sim_stackitem_null,
    )
    if simGetStackItemType(stackHandle, -1) == sim_stackitem_null:
        simPopStackItem(stackHandle, 1)
        return None
    else:
        raise RuntimeError('expected nil')

def read_bool(stackHandle):
    from coppeliasim.lib import (
        simGetStackBoolValue,
        simPopStackItem,
    )
    value = ctypes.c_bool()
    if simGetStackBoolValue(stackHandle, ctypes.byref(value)) == 1:
        simPopStackItem(stackHandle, 1)
        return value.value
    else:
        raise RuntimeError('expected bool')

def read_int(stackHandle):
    from coppeliasim.lib import (
        simGetStackInt32Value,
        simPopStackItem,
    )
    value = ctypes.c_int()
    if simGetStackInt32Value(stackHandle, ctypes.byref(value)) == 1:
        simPopStackItem(stackHandle, 1)
        return value.value
    else:
        raise RuntimeError('expected int')

def read_long(stackHandle):
    from coppeliasim.lib import (
        simGetStackInt64Value,
        simPopStackItem,
    )
    value = ctypes.c_longlong()
    if simGetStackInt64Value(stackHandle, ctypes.byref(value)) == 1:
        simPopStackItem(stackHandle, 1)
        return value.value
    else:
        raise RuntimeError('expected int64')

def read_double(stackHandle):
    from coppeliasim.lib import (
        simGetStackDoubleValue,
        simPopStackItem,
    )
    value = ctypes.c_double()
    if simGetStackDoubleValue(stackHandle, ctypes.byref(value)) == 1:
        simPopStackItem(stackHandle, 1)
        return value.value
    else:
        raise RuntimeError('expected double')

def read_string(stackHandle):
    from coppeliasim.lib import (
        simGetStackStringValue,
        simReleaseBuffer,
        simPopStackItem,
    )
    string_size = ctypes.c_int()
    string_ptr = simGetStackStringValue(stackHandle, ctypes.byref(string_size))
    string_value = ctypes.string_at(string_ptr, string_size.value)
    simPopStackItem(stackHandle, 1)
    value = string_value.decode('utf-8')
    simReleaseBuffer(string_ptr)
    return value

def read_dict(stackHandle):
    from coppeliasim.lib import (
        simGetStackTableInfo,
        simGetStackSize,
        simUnfoldStackTable,
        simMoveStackItemToTop,
        sim_stack_table_map,
        sim_stack_table_empty,
    )
    d = dict()
    info = simGetStackTableInfo(stackHandle, 0)
    if info != sim_stack_table_map and info != sim_stack_table_empty:
        raise RuntimeError('expected a map')
    oldsz = simGetStackSize(stackHandle)
    simUnfoldStackTable(stackHandle)
    n = (simGetStackSize(stackHandle) - oldsz + 1) // 2
    for i in range(n):
        simMoveStackItemToTop(stackHandle, oldsz - 1)
        k = read_value(stackHandle)
        simMoveStackItemToTop(stackHandle, oldsz - 1)
        d[k] = read_value(stackHandle)
    return d

def read_list(stackHandle):
    from coppeliasim.lib import (
        simGetStackSize,
        simUnfoldStackTable,
        simMoveStackItemToTop,
    )
    l = list()
    oldsz = simGetStackSize(stackHandle)
    simUnfoldStackTable(stackHandle)
    n = (simGetStackSize(stackHandle) - oldsz + 1) // 2
    for i in range(n):
        simMoveStackItemToTop(stackHandle, oldsz - 1)
        read_value(stackHandle)
        simMoveStackItemToTop(stackHandle, oldsz - 1)
        l.append(read_value(stackHandle))
    return l

def read_table(stackHandle):
    from coppeliasim.lib import (
        simGetStackTableInfo,
        sim_stack_table_map,
        sim_stack_table_empty,
    )
    sz = simGetStackTableInfo(stackHandle, 0)
    if sz >= 0:
        return read_list(stackHandle)
    elif sz == sim_stack_table_map or sz == sim_stack_table_empty:
        return read_dict(stackHandle)

def read_value(stackHandle):
    from coppeliasim.lib import (
        simGetStackItemType,
        sim_stackitem_null,
        sim_stackitem_double,
        sim_stackitem_bool,
        sim_stackitem_string,
        sim_stackitem_table,
        sim_stackitem_integer,
    )
    item_type = simGetStackItemType(stackHandle, -1)
    if item_type == sim_stackitem_null:
        value = read_null(stackHandle)
    elif item_type == sim_stackitem_double:
        value = read_double(stackHandle)
    elif item_type == sim_stackitem_bool:
        value = read_bool(stackHandle)
    elif item_type == sim_stackitem_string:
        value = read_string(stackHandle)
    elif item_type == sim_stackitem_table:
        value = read_table(stackHandle)
    elif item_type == sim_stackitem_integer:
        value = read_long(stackHandle)
    else:
        raise RuntimeError(f'unexpected stack item type: {item_type}')
    return value

def read(stackHandle):
    from coppeliasim.lib import (
        simGetStackSize,
        simMoveStackItemToTop,
        simPopStackItem,
    )
    stack_size = simGetStackSize(stackHandle)
    tuple_data = []
    for i in range(stack_size):
        simMoveStackItemToTop(stackHandle, 0)
        tuple_data.append(read_value(stackHandle))
    simPopStackItem(stackHandle, 0) # clear all
    return tuple(tuple_data)

def write_null(stackHandle, value):
    from coppeliasim.lib import (
        simPushNullOntoStack,
    )
    simPushNullOntoStack(stackHandle)

def write_double(stackHandle, value):
    from coppeliasim.lib import (
        simPushDoubleOntoStack,
    )
    simPushDoubleOntoStack(stackHandle, value)

def write_bool(stackHandle, value):
    from coppeliasim.lib import (
        simPushBoolOntoStack,
    )
    simPushBoolOntoStack(stackHandle, value)

def write_int(stackHandle, value):
    from coppeliasim.lib import (
        simPushInt32OntoStack,
    )
    simPushInt32OntoStack(stackHandle, value)

def write_string(stackHandle, value):
    from coppeliasim.lib import (
        simPushStringOntoStack,
    )
    simPushStringOntoStack(stackHandle, value.encode('utf-8'), len(value))

def write_dict(stackHandle, value):
    from coppeliasim.lib import (
        simPushTableOntoStack,
        simInsertDataIntoStackTable,
    )
    simPushTableOntoStack(stackHandle)
    for k, v in value.items():
        write_value(stackHandle, k)
        write_value(stackHandle, v)
        simInsertDataIntoStackTable(stackHandle)

def write_list(stackHandle, value):
    from coppeliasim.lib import (
        simPushTableOntoStack,
        simInsertDataIntoStackTable,
    )
    simPushTableOntoStack(stackHandle)
    for i, v in enumerate(value):
        write_value(stackHandle, i + 1)
        write_value(stackHandle, v)
        simInsertDataIntoStackTable(stackHandle)

def write_value(stackHandle, value):
    if value is None:
        write_null(stackHandle, value)
    elif isinstance(value, float):
        write_double(stackHandle, value)
    elif isinstance(value, bool):
        write_bool(stackHandle, value)
    elif isinstance(value, int):
        write_int(stackHandle, value)
    elif isinstance(value, str):
        write_string(stackHandle, value)
    elif isinstance(value, dict):
        write_dict(stackHandle, value)
    elif isinstance(value, list):
        write_list(stackHandle, value)
    else:
        raise RuntimeError(f'unexpected type: {type(value)}')

def debug(stackHandle, info = None):
    from coppeliasim.lib import (
        simGetStackSize,
        simDebugStack,
    )
    info = '' if info is None else f' {info} '
    n = (70 - len(info)) // 2
    m = 70 - len(info) - n
    print('#' * n + info + '#' * m)
    for i in range(simGetStackSize(stackHandle)):
        simDebugStack(stackHandle, i)
    print('#' * 70)

def write(stackHandle, tuple_data):
    for item in tuple_data:
        write_value(stackHandle, item)
