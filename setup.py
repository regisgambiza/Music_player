from cx_Freeze import setup, Executable

setup(
    name="Ano Music Player",
    version="1.0",
    description="Your application description",
    executables=[Executable("main.py", base=None)],
)
