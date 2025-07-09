import locale

def get_system_language():
    try:
        return locale.getdefaultlocale()[0]
    except Exception:
        return "tr_TR"

def format_bytes(size):
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"
