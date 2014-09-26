#!/usr/bin/env python

"""
Copyright (C) 2012 (AHORA FUNCIONA!!!)
Tomador de datos de radio para Python. Inspirado en:
Copyright (C) 2008, Roger Fearick, University of Cape Town 
Guarda archivos de datos tomados de la entrada derecha de microfono
la carpeta se llama dat/ y los archivos 'dat%4d.d'
las variables a cambiar son maxavcount y logy
"""

import sys
from numpy import *
import numpy.fft as FFT
import pyaudio
import os           #para que reconozca os.system('instrucciones en consola')
import datetime     #para imprimir fecha
import time         #para manejar tiempos

# audio setup
CHUNK = 8192    # input buffer size in frames
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000    # depends on sound card: 96000 might be possible

# scope configuration
soundbuffersize=CHUNK
samplerate=float(RATE)

def Interactivo(): #solo por si no me acuerdo
    os.system('clear') 
    print '______________________OSCILOTRON v1.0______________________'
    #esta parte sirve para que de chance a guardar datos pasados y no borrarlos (ES OPCIONAL)
    #"""
    print '\nVoy a borrar las carpetas /img y /dat y su contenido...'
    print '\t(Enter para continuar)'
    ui.name = raw_input()
    os.system('rm -R dat img')
    os.system('mkdir dat img')
    #"""

    print 'Que tipo de muestreo:' 
    print '\t0->fft \n\t1->continuo\n\tg->gran integracion'
    tipo=raw_input()

    if tipo == '0':
        print 'Escogido: modo espectro integrado ('+str(ui.maxavcount)+' muestras por intervalo)'
        print 'Cuantos intervalos:  '
        cuantos=int(raw_input())
        print '--iniciando toma de datos...'
        ui.Espectro(cuantos)  #cuantos bines temporales se quieren
        print '...fin--'
        os.system('/bin/bash espectro.script') #elque hace el videito, osea que se puede quitar

    if tipo == '1':
        print 'Escogido: modo continuo' 
        print 'Cuantos intervalos:  '
        cuantos=int(raw_input())
        print '--iniciando toma de datos...'
        for j in range(cuantos):
            ui.Continuo()
        print '...fin--'
        os.system('/bin/bash continuo.script') #elque hace el videito, lo mismo.

    if tipo == 'g' or tipo == 'G':
        print 'Escogido: modo gran integracion' 
        print 'Cuantos frames:  '
        cuantos=int(raw_input())
        ui.GranInt(cuantos)
        print '--iniciando integracion...'
        ui.Espectro(1)
        print '...fin--'
        os.system('/bin/bash integrado.script') #elque hace el videito, lo mismo.

    if (tipo != '0' and tipo != '1' and tipo != 'g' and tipo != 'G'):
        print 'ES CERO (0), ES UNO (1) O ES G (g)... ErrorM'   
    print '___________________________________________________________'


#+og para guardar los datos en un momento determinado
def guardar_datos(X, Y, f):
    """
    Guarda un archivo x, y, indice... con el formato 'datos%4d.d'
    """
    global A
    A =  zip(X, Y)
    A = array(A)
    if len(f)==1: f='000'+f
    if len(f)==2: f='00'+f
    if len(f)==3: f='0'+f  
    nombre = 'dat/datos' + f +'.d'
    savetxt(nombre, A)
    return
#fin
  
class Integrando():
    """
    La clase que integra la senal
    """
    def __init__(self, *args):
        self.name=str('')
        self.j=1
        self.avcount=1          #contador para frames de integracion DEBE COMENZAR DE 1, SINO ERROR
        #para maxavcount -> minimo 2, mediocre 5, maso 10, bonito 25 (entre mas, mas tiempo)
        self.maxavcount=10       #valor de frames integrados MINIMO 2
        self.logy = 0             #poner '0' para escala natural, '1' logaritmica
        self.datastream=None    #stream
        
        self.dt=1.0/samplerate
        self.df=1.0/(soundbuffersize*self.dt)
        self.f = arange(0.0, samplerate, self.df)
        self.a = 0.0*self.f
   
    def Stream(self,datas):
        self.datastream = datas

    def GranInt(self,frames):
        self.maxavcount = frames

    def Espectro(self, frames):
        while self.j< frames+1:   #recorre hasta que sea igual a la cantidad de frames 
            if self.datastream == None: return
            x=self.datastream.read(CHUNK)
            X=fromstring(x,dtype='h')
            if len(X) == 0: return
            P=array(X,dtype='d')
            i=0
            R=P[0::2]
            lenX=len(R)
            if lenX == 0: return
                        
            B = abs(FFT.fft(R))
            B = B*B #esta es para ver el espectro de potencia
            self.f= 2 *44.12* FFT.fftfreq(lenX, 1) #aqui se calibra el espectro, por nyquist
            #self.f= 2 * FFT.fftfreq(lenX, self.dt)

            	
            if self.logy==1:
                Pm=log10(B)*10.0+20.0#60.0
            else:
                Pm=B
        
            if self.avcount==1:
                sumPm=Pm
            else:
                sumPm=sumPm+Pm
        
            if self.avcount == self.maxavcount: 
               self.a = sumPm/self.maxavcount
               self.avcount = 1
               ns = len(self.a)
               char = str(self.j)
               guardar_datos(self.f[0:ns/2], self.a[:ns], char)
               #print self.j imprime en pantalla el frame que va (pa depuracion)
               self.j=self.j+1
               #self.f=0.0*self.f
               #self.a=0.0*self.a
               sumPm=0
       
            self.avcount+=1
    	
    def Continuo(self):
        if self.datastream == None: return
        x=self.datastream.read(CHUNK)
        X=fromstring(x,dtype='h')
        if len(X) == 0: return
        P=array(X,dtype='d')/32768.0
       
        val=0.01    #Modificar este valor para ver solo picos de corriente es el triger, esta en [-1:1]
        i=0
        R=P[0::2]
          
        for i in range(len(R)-1):
            if R[i]<val and R[i+1]>=val: break
        
        if i > len(R)-2: i=0
        
        self.a=R[i:]
 
        ns=len(self.a)
        char=str(self.j)
        guardar_datos(self.f[0:ns], self.a[:ns], char)
        self.j=self.j+1
        #print self.j
       
# open sound card data stream
p = pyaudio.PyAudio()
stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                input = True,
                frames_per_buffer = CHUNK)

# iayesta za mierda! 
ui=Integrando()
ui.Stream(stream)

arg = len(sys.argv)

if (arg !=1 and arg !=4):
    sys.exit('Argumentos invalidos (ninguno o -c tipo cuantos)')
    exit    
  
if arg == 1:
    Interactivo();   
   
if arg == 4:
    if sys.argv[1] == '-c':
        tipo = str(sys.argv[2])
        cuantos = int(sys.argv[3])        
        if tipo == '0':
            ui.Espectro(cuantos)  #cuantos bines temporales se quieren
            os.system('/bin/bash espectro.script') #elque hace el videito, osea que se puede quitar

        if tipo == '1':
            for j in range(cuantos):
                ui.Continuo()
            os.system('/bin/bash continuo.script') #elque hace el videito, lo mismo.

        if tipo == 'g' or tipo == 'G':
            ui.GranInt(cuantos)
            ui.Espectro(1)
            os.system('/bin/bash integrado.script') #elque hace el videito, lo mismo.
        
        if (tipo != 'g' and tipo != 'G' and tipo != '1' and tipo != '0'):
            sys.exit('Argumentos invalidos (ninguno o -c tipo cuantos)')
            exit
         
        print'listo!'

stream.stop_stream()
stream.close()
p.terminate()
