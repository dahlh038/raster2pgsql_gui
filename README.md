# raster2pgsql_gui
Downloadable .py file that makes a raster2pgsql_gui.exe file
Made on Windows 11
You will need to pip install pyinstaller
In the command line, navigate to where you have the file downloaded, then run:
python -m PyInstaller --onefile --windowed raster2pgsql_gui.py
Next, run the command for where you want the gui application to live. Ex:
move dist\raster2pgsql_gui.exe "C:\Program Files\PostgreSQL\18\bin\raster2pgsql_gui.exe"

Made with the intent to connect with pgAdmin4.
Used ChatGPT to help with coding.
Runs very slowly, if you have any suggestions, please let me know!
