from pytube import YouTube
from tkinter import *

def download():
    if mainInput.get():
        if audioOption.get() and videoOption.get():
            errorLabel.config(text='Debes seleccionar solo una opción', font=('Arial', 14), fg='red', bg='gray')
        elif audioOption.get():
            try:
                yt = YouTube(mainInput.get())
                yt.streams.filter(only_audio=True).order_by('abr').desc().first().download()
                errorLabel.config(text='Descarga exitosa de audio', font=('Arial', 14), fg='greenyellow', bg='gray')
            except:
                errorLabel.config(text='Error al descargar el audio', font=('Arial', 14), fg='red', bg='gray')
        elif videoOption.get():
            try:
                yt = YouTube(mainInput.get())
                yt.streams.filter(only_video=True , resolution='720p').first().download()
                errorLabel.config(text='Descarga exitosa de video', font=('Arial', 14), fg='greenyellow', bg='gray')
            except:
                errorLabel.config(text='Error al descargar el video', font=('Arial', 14), fg='red', bg='gray')
        else:
            errorLabel.config(text='Debes seleccionar al menos una opción', font=('Arial', 14), fg='red', bg='gray')

    else: 
        errorLabel.config(text='Debes ingresar una URL', font=('Arial', 14), fg='red', bg='gray')


# interfaz con tkinder
    
root = Tk()

root.geometry('450x300')
root.title('YT Downloader')

myLabel = Label(root, text='Ingresa URL')
myLabel.pack()

errorLabel = Label(root, text='', fg='red', font=('Arial', 14))
errorLabel.pack(side='bottom')

mainInput = Entry(root, width=40, border=2)
mainInput.pack()

audioOption = BooleanVar()
audioCheck = Checkbutton(root, text='audio (HD)', variable=audioOption)
audioCheck.pack()

videoOption = BooleanVar()
videoCheck = Checkbutton(root, text='video (720p HD)', variable=videoOption)
videoCheck.pack(padx='20')

video = Button(root, text='Descargar', pady=10, padx=20, bg='lightgray', command=download)
video.pack()

root.mainloop()




