import ctypes
import functools


def load():
    call('require', ('scriptClientBridge',))


@functools.cache
def getTypeHints(func):
    try:
        import calltip
    except ModuleNotFoundError:
        from pathlib import Path
        import sys
        zmqRemoteApiToolsPath = str(Path(__file__).parent.parent.parent / 'zmqRemoteApi' / 'tools')
        if zmqRemoteApiToolsPath not in sys.path:
            sys.path.append(zmqRemoteApiToolsPath)
        try:
            import calltip
        except ModuleNotFoundError:
            print('warning: zmqRemoteApi.tools.calltip module not found (set PYTHONPATH to /path/to/zmqRemoteApi/tools to fix this)')
            return (None, None)
    c = call('sim.getApiInfo', [-1, func], (('int', 'string'), ('string')))
    if not c:
        return (None, None)
    c = c.split('\n')[0]
    fd = calltip.FuncDef.from_calltip(c)
    return (
        tuple(item.type for item in fd.in_args),
        tuple(item.type for item in fd.out_args),
    )


def call(func, args, typeHints=None):
    if typeHints is None:
        typeHints = getTypeHints(func)
    from coppeliasim.lib import (
        simCreateStack,
        simCallScriptFunctionEx,
        simReleaseStack,
        sim_scripttype_sandboxscript,
    )
    import coppeliasim.stack as stack
    stackHandle = simCreateStack()
    stack.write(stackHandle, args, typeHints[0])
    s = sim_scripttype_sandboxscript
    f = ctypes.c_char_p(f'{func}@lua'.encode('ascii'))
    r = simCallScriptFunctionEx(s, f, stackHandle)
    if r == -1:
        if False:
            what = f'simCallScriptFunctionEx({s}, {func!r}, {args!r})'
        else:
            what = 'simCallScriptFunctionEx'
        raise Exception(f'{what} returned -1')
    ret = stack.read(stackHandle, typeHints[1])
    simReleaseStack(stackHandle)
    if len(ret) == 1:
        return ret[0]
    elif len(ret) > 1:
        return ret


def getObject(name, _info=None):
    ret = type(name, (), {})
    if not _info:
        _info = call('scriptClientBridge.info', [name])
    for k, v in _info.items():
        if not isinstance(v, dict):
            raise ValueError('found nondict')
        if len(v) == 1 and 'func' in v:
            if f'{name}.{k}' == 'sim.getScriptFunctions':
                setattr(ret, k, lambda scriptHandle:
                        type('', (object,), {
                            '__getattr__':
                                lambda _, func:
                                    lambda *args:
                                        call('sim.callScriptFunction', (func, scriptHandle) + args)
                        })())
                continue
            setattr(ret, k, lambda *a, func=f'{name}.{k}': call(func, a))
        elif len(v) == 1 and 'const' in v:
            setattr(ret, k, v['const'])
        else:
            setattr(ret, k, getObject(f'{name}.{k}', _info=v))
    return ret


def require(obj):
    call('scriptClientBridge.require', [obj])
    o = getObject(obj)
    return o
