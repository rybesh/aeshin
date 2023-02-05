def truncate(content, length=100, suffix="..."):
    if len(content) <= length:
        return content
    else:
        return " ".join(content[: length + 1].split(" ")[0:-1]) + suffix
