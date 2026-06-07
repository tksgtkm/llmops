from jinja2 import Template

def main() -> None:
    source = """{% if message %}メッセージがあります。: {{ message }}{% endif %}"""
    template = Template(source=source)

    print("1.", template.render(message="hello"))
    print("2.", template.render())

if __name__ == "__main__":
    main()