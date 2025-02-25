# -*- coding: utf-8 -*-
'''
.. py:module:: AITA toolbox
Created on 3 juil. 2015
Toolbox for data obtained using G50 Automatique Ice Texture Analyser (AITA) provide by :
Russell-Head, D.S., Wilson, C., 2001. Automated fabric analyser system for quartz and ice. J. Glaciol. 24, 117–130

@author: Thomas Chauve
@contact: thomas.chauve@lgge.obs.ujf-grenoble.fr
@license: CC-BY-CC
'''

import numpy as np
import matplotlib.pyplot as plt
import micro2d as mi2d
import image2d as im2d
import math
import pylab
from skimage import io
import datetime
import random
import scipy
from scipy.stats import gaussian_kde
import colorsys

class aita(object):
    '''
	"aita" is a python class to analyse output from G50-AITA analyser.
	It provide an environnement to plot data, to create inpur for CraFT code,...
	
	This toolbox is running on python3 and need various packages :
	
	    :library: numpy	    
	    :library: matplotlib
	    :library: math
	    :library: pylab
	    :library: skimage
	    :library: datetime
	    :library: random
	    :library: colosys
	    :library: image2d (see below)	    
    '''
    pass
    
    def __init__(self,phi1_field,phi_field,qua_field,micro_field,resolution=1):
        '''        
        :param phi1_field: Euler angle phi1 map
        :param phi_field: Euler angle phi map
        :param qua_field: quality facteur map
        :param resolution: spatial step size (mm); default = 1 mm
        :param micro_field: microstructure (0 background, 1 grain boundary)
        
        :type phi1_field np.array
        :type phi_field np.array
        :type qua_field: np.array
        :type resolution: float
        :type micro_adress: np.array
        
        :return: aita object output
        :rtype: aita
                             
        .. note:: Bunge Euler Angle convention is used (phi1,phi,phi2) ,phi2 is not compute as during optical measurement phi2 is not know.
        '''
        
        # create image object from data
        self.phi1=im2d.image2d(phi1_field,resolution)
        self.phi=im2d.image2d(phi_field,resolution)
        self.qua=im2d.image2d(qua_field,resolution)
        
        # create microstructure
        self.micro=mi2d.micro2d(micro_field,resolution)
        self.grains=self.micro.grain_label()
        
        # replace grains boundary with NaN number
        self.grains.field=np.array(self.grains.field,float)
        idx=np.where(self.micro.field==1)
        self.grains.field[idx]=np.nan

        print ("Sucessfull aita build !")  
        
    def crop(self):
        '''
        Crop function to select the area of interest
        
        :return: crop aita object
        :rtype: aita
        :Exemple: >>> data.crop()
        
        .. note:: clic on the top left corner and bottom right corner to select the area
        '''
        
        # plot the data
        h=self.phi.plot()
        # select top left and bottom right corner for crop
        print('Select top left and bottom right corner for crop :')
        x=np.array(pylab.ginput(2))/self.phi.res
        plt.close("all")
        # create x and Y coordinate
        
        xx=[x[0][0],x[1][0]]
        yy=[x[0][1],x[1][1]]
        # size of the initial map
        ss=np.shape(self.phi.field)
        # find xmin xmax ymin and ymax
        xmin=np.ceil(np.min(xx))
        xmax=np.floor(np.max(xx))
        ymin=ss[0]-np.ceil(np.max(yy))
        ymax=ss[0]-np.floor(np.min(yy))
        
        # crop the map
        self.phi.field=self.phi.field[ymin:ymax, xmin:xmax]
        self.phi1.field=self.phi1.field[ymin:ymax, xmin:xmax]
        self.qua.field=self.qua.field[ymin:ymax, xmin:xmax]
        self.micro.field=self.micro.field[ymin:ymax, xmin:xmax]
        self.grains=self.micro.grain_label()
        
        # replace grains boundary with NaN number
        self.grains.field=np.array(self.grains.field,float)
        idx=np.where(self.micro.field==1)
        self.grains.field[idx]=np.nan
        
    def fliplr(self):
        '''
        Applied an horizontal miror to the data
        
        :return:  aita object with an horizontal miror
        :rtype: aita
        :Exemple: >>> data.fliplr()
        '''
        
        # horizontal miror (fliplr) on all the data in self
        self.phi.field=np.fliplr(self.phi.field)
        self.phi1.field=np.mod(math.pi-np.fliplr(self.phi1.field),2*math.pi) # change phi1 angle by pi-phi1 modulo 2*pi
        self.qua.field=np.fliplr(self.qua.field)
        self.micro.field=np.fliplr(self.micro.field)
        self.grains.field=np.fliplr(self.grains.field)
        
    def rot180(self):
        '''
        Rotate the data of 180 degree
        
        :return: crop aita object
        :rtype: aita
        :Exemple: >>> data.rot180()
        '''
        
        # rotate the position of the data if 180 degre
        self.phi.field=np.flipud(np.fliplr(self.phi.field))
        self.phi1.field=np.mod(math.pi+np.flipud(np.fliplr(self.phi1.field)),2*math.pi) # rotate the c-axis : phi1 = pi + phi1 mod(2*pi)
        self.qua.field=np.flipud(np.fliplr(self.qua.field))
        self.micro.field=np.flipud(np.fliplr(self.micro.field))
        self.grains.field=np.flipud(np.fliplr(self.grains.field))
        
    def filter(self,value):
        ''' 
        Remove data of bad quality
        
        :param value: limit quality value between 0 to 100
        :type value: int
        :return: data object with no orientation with quality value under threshold
        :rtype: aita
        :Exemple: >>> data.filter(75)
        '''
        # find where quality<value
        x=np.where(self.qua.field < value)
        self.phi.field[x]=np.NAN
        self.phi1.field[x]=np.NAN
        
    def mean_grain(self):
        '''
        Compute the mean orientation inside the grain
        
        :return: data with only one orientation per grains, the mean orientation
        :rtype: aita
        :Exemple: >>> data.mean_orientation()
        '''
        # number of grain
        nb_grain=int(np.nanmax(self.grains.field))
        # loop on all the grain
        for i in list(xrange(nb_grain+1)):
            # find the pixel inside the grain i
            idx=np.where(self.grains.field==i)
            # compute the mean value of phi1 and phi and replace the value in the map
            self.phi.field[idx]=np.nanmean(self.phi.field[idx])
            self.phi1.field[idx]=np.nanmean(self.phi1.field[idx])
        
    def imresize(self,res):
        '''
        Resize the data
        
        :param res: the new resolution wanted in millimeter (mm)
        :type res: float
        :return: data with the resolution wanted
        :rtype: aita
        :Exemple: >>> data.imresize(0.25)
        '''
        self.phi.imresize(res)
        self.phi1.imresize(res)
        self.qua.imresize(res)
        self.grains.imresize(res)
        
        # make larger the boundaries to keep them
        self.micro.field=scipy.ndimage.binary_dilation(self.micro.field, iterations=np.int32(res/(2*self.micro.res)))
        # resize
        self.micro.imresize(res)
        
    def craft(self,nameId):
        '''
        Create the inputs for craft
        
        :param nameId: name of the prefixe used for craft files
        :type nameId: str
        :return: create file : nameId_micro.vtk, nameId.phase, nameId.in, nameId.load, nameId.output
        :Exemple: >>> data.craft('manip01')
        
        .. note:: nameId.load, nameId.output need to be rewrite to get a correct loading and the output wanted
           
        .. note:: nameId.in need to be adapt depending of your folder structure used for craft
            
        .. note:: NaN orientation value are removed by the closest orientation
        '''
        ##############################################
        # remove the grain boundary (remove NaN value)
        ##############################################
        # find where are the NaN Value corresponding to the grain boundary
        idx=np.where(np.isnan(self.grains.field))
        # while NaN value are in the microstructure we replace by an other value ...
        while np.size(idx)>0:
            # for all the pixel NaN
            for i in list(xrange(np.shape(idx)[1])):
                # if the pixel is at the bottom line of the sample, we choose the pixel one line upper ...
                if idx[0][i]==0:
                    k=idx[0][i]+1
                #... else we choose the pixel one line higher.
                else:
                    k=idx[0][i]-1
                # if the pixel is at the left side of the sample, we choose the pixel at its right  ...
                if idx[1][i]==0:
                    kk=idx[1][i]+1
                # else we choose the pixel at its left.
                else:
                    kk=idx[1][i]-1
                # Replace the value by the value of the neighbor select just before
                self.phi.field[idx[0][i], idx[1][i]]= self.phi.field[k, kk]
                self.phi1.field[idx[0][i], idx[1][i]]= self.phi1.field[k, kk]
                self.grains.field[idx[0][i], idx[1][i]]= self.grains.field[k, kk]
                # re-evaluate if there is sill NaN value inside the microstructure
            idx=np.where(np.isnan(self.grains.field))# re-evaluate the NaN
            
        # find the value of the orientation for each phase
        phi1=[]
        phi=[]
        phi2=[]
        for i in list(xrange(np.max(np.int32(self.grains.field)+1))):
            idx=np.where(np.int32(self.grains.field)==i)
            if np.size(idx)!=0:
                phi1.append(self.phi1.field[idx[0][0]][idx[1][0]])
                phi.append(self.phi.field[idx[0][0]][idx[1][0]])
                phi2.append(random.random()*2*math.pi)
            else:
                phi1.append(np.nan)
                phi.append(np.nan)
                phi2.append(np.nan)
        ################################   
        # Write the microstructure input
        ################################
        # size of the map
        ss=np.shape(self.grains.field)
        # open micro.vtk file
        micro_out=open(nameId+'_micro.vtk','w')
        # write the header of the file
        micro_out.write('# vtk DataFile Version 3.0 ' + str(datetime.date.today()) + '\n')
        micro_out.write('craft output \n')
        micro_out.write('ASCII \n')
        micro_out.write('DATASET STRUCTURED_POINTS \n')
        micro_out.write('DIMENSIONS ' + str(ss[1]) + ' ' + str(ss[0]) +  ' 1\n')
        micro_out.write('ORIGIN 0.000000 0.000000 0.000000 \n')
        micro_out.write('SPACING ' + str(self.grains.res) + ' ' + str(self.grains.res) + ' 1.000000 \n')
        micro_out.write('POINT_DATA ' + str(ss[0]*ss[1]) + '\n')
        micro_out.write('SCALARS scalars float \n')
        micro_out.write('LOOKUP_TABLE default \n')
        for i in list(xrange(ss[0]))[::-1]:
            for j in list(xrange(ss[1])):
                micro_out.write(str(int(self.grains.field[i][j]))+' ')
            micro_out.write('\n')        
        micro_out.close()
        ################################   
        ##### Write the phase input ####
        ################################
        phase_out=open(nameId+'.phase','w')
        phase_out.write('#------------------------------------------------------------\n')
        phase_out.write('# Date ' + str(datetime.date.today()) + '      Manip: ' + nameId + '\n')
        phase_out.write('#------------------------------------------------------------\n')
        phase_out.write('# This file give for each phase \n# *the matetial \n# *its orientation (3 euler angles)\n')
        phase_out.write('#\n#------------------------------------------------------------\n')
        phase_out.write('# phase    material       phi1    Phi   phi2\n')
        phase_out.write('#------------------------------------------------------------\n')
        for i in list(xrange(np.size(phi))):
            if 1-np.isnan(phi[i]):
                phase_out.write(str(i) + '          0              ' + str(phi1[i]) + ' ' + str(phi[i]) + ' ' + str(phi2[i]) + '\n');  
        phase_out.close()
        ################################
        # Write an exemple of load file##
        ################################
        out_load=open(nameId + '.load','w');
        out_load.write('#------------------------------------------------------------\n')
        out_load.write('# Date ' + str(datetime.date.today()) + '      Manip: ' + nameId + '\n')
        out_load.write('#------------------------------------------------------------\n')
        out_load.write('# choix du type de chargement \n')
        out_load.write('# direction contrainte imposée: S \n')
        out_load.write('# contrainte imposée:          C \n')
        out_load.write('# déformation imposée:         D \n')
        out_load.write('C\n')
        out_load.write('#------------------------------------------------------------\n')
        out_load.write('# nb de pas    temps        direction            facteur\n')
        out_load.write('#                            11 22 33 12 13 23\n')
        out_load.write('                5.            0  1  0  0  0  0    -0.5\n')
        out_load.write('5.            100.          0  1  0  0  0  0    -0.5\n')
        out_load.write('#\n')
        out_load.write('#------------------------------------------------------------\n')
        out_load.close()
        ###################################
        # Write an exemple of output file #
        ###################################    
        out_output=open(nameId + '.output','w')
        out_output.write('#------------------------------------------------------------\n')
        out_output.write('# Date ' + str(datetime.date.today()) + '      Manip: ' + nameId + '\n')
        out_output.write('#------------------------------------------------------------\n')
        out_output.write('equivalent stress image = yes 10,60,100\n')
        out_output.write('equivalent strain image = yes 10,60,100\n')
        out_output.write('#\n')
        out_output.write('stress image = yes 10,60,100\n')
        out_output.write('strain image = yes 10,60,100\n')
        out_output.write('#\n')
        out_output.write('backstress image = yes 10,60,100\n')
        out_output.write('#\n')
        out_output.write('strain moment = yes 5:100\n')
        out_output.write('stress moment = yes 5:100\n')
        out_output.write('im_format=vtk\n')
        out_output.close()  
        #####################################
        ## Write the input file for craft####
        #####################################
        out_in=open(nameId + '.in','w');
        out_in.write('#------------------------------------------------------------\n')
        out_in.write('# Date ' + str(datetime.date.today()) + '      Manip: ' + nameId + '\n')
        out_in.write('#------------------------------------------------------------\n')
        out_in.write('#\n')
        out_in.write('#\n')
        out_in.write('#------------------------------------------------------------\n')
        out_in.write('# name of the file of the image of the microstructure\n')
        out_in.write('microstructure=../'+ nameId+'_micro.vtk\n')
        out_in.write('#\n')
        out_in.write('#------------------------------------------------------------\n')
        out_in.write('# name of the file of the description of phases\n')
        out_in.write('phases=../'+nameId+'.phase\n')
        out_in.write('#\n')
        out_in.write('#------------------------------------------------------------\n')
        out_in.write('# name of the file describing the materials the phases are made of:\n')
        out_in.write('materials=../../../../Ice_Constitutive_Law/glace3_oc2_5mai2011.mat\n')
        out_in.write('#\n')
        out_in.write('#------------------------------------------------------------\n')
        out_in.write('# file of the loading conditions:\n')
        out_in.write('loading=../'+nameId + '.load\n')
        out_in.write('#\n')
        out_in.write('#------------------------------------------------------------\n')
        out_in.write('# file telling the outputs one wants to obtain:\n')
        out_in.write('output=../' +nameId + '.output\n')
        out_in.write('#\n')
        out_in.write('#------------------------------------------------------------\n')
        out_in.write('# The parameter C0 has to be set by craft:\n')
        out_in.write('C0=auto\n')
        out_in.write('#\n')
        out_in.write('#------------------------------------------------------------\n')
        out_in.write('# # required precision for equilibrium and for loading conditions:\n')
        out_in.write('precision=1.e-4, 1.e-4\n')
        out_in.write('#------------------------------------------------------------\n')
        out_in.close()
    
    def plotpdf(self,peigen=False,select_grain=False,grainlist=[],allpixel=False,filter=0):
        '''
        Plot pole figure for c-axis (0001)
        
        :param peigen: Plot the eigenvalues and eigenvectors on the pole figure (default = False)
        :type peigen: bool
        :param select_grain: select the grains use for the pole figure
        :type select_grain: bool
        :param grainlist: give the list of the grainId you want to plot
        :type grainlist: list
        :param allpixel: do you want plot all the pixel ?
        :type allpixel: bool
        :param filter: remove the pixel were the density is the lower, in fact the filter % lower point. (filter between 0 and 100)
        :type filter: float
        :return: eigenvector a1, a2, a3
        :rtype: float
        :return: pole figure image
        :rtype: matplotlib figure
        :Exemple:
            >>> a1, a2, a3 = data.plotpdf(peigen=True)
            >>> plt.show()
        '''
        
        if select_grain:
            if grainlist==[]:
                plt.imshow(self.grains.field,aspect='equal')
                plt.waitforbuttonpress()
                print('midle mouse clic when you are finish')
                #grain wanted for the plot
                id=np.int32(np.array(pylab.ginput(0)))
                plt.close('all')
                # find the label of grain
                label=self.grains.field[id[:,1],id[:,0]]
            else:
                label=grainlist
            tazi=[]
            tcol=[]
            for i in list(xrange(len(label))):
                idx=np.where(self.grains.field==label[i])
                tazi.append(list(np.mod(self.phi1.field[idx[0],idx[1]]-math.pi/2,2*math.pi)))
                tcol.append(list(self.phi.field[idx[0],idx[1]]))
                
            azi=np.transpose(np.concatenate(np.array(tazi)))
            col=np.transpose(np.concatenate(np.array(tcol)))
        else:
            # compute azimuth and colatitude
            azi=np.mod(self.phi1.field.reshape((-1,1))-math.pi/2,2*math.pi)
            col=self.phi.field.reshape((-1,1))

        # compute [xc,yc,zc] the coordinate of the c-axis
        xc = np.multiply(np.cos(azi),np.sin(col))
        yc = np.multiply(np.sin(azi),np.sin(col))
        zc = np.cos(col)
        
        # compute components of the orientation tensor
        # corection vicious bug : if you are not using np.float128 sommetimes the sum is wrong (different of the loof 'for' and wrong), you need to have a better precision in your definition of a float.
        a11 = np.float32(np.nanmean(np.float128(np.multiply(xc,xc))))
        a22 = np.float32(np.nanmean(np.float128(np.multiply(yc,yc))))
        a33 = np.float32(np.nanmean(np.float128(np.multiply(zc,zc))))
        a12 = np.float32(np.nanmean(np.float128(np.multiply(xc,yc))))
        a13 = np.float32(np.nanmean(np.float128(np.multiply(xc,zc))))
        a23 = np.float32(np.nanmean(np.float128(np.multiply(yc,zc))))
        
        orientation_tensor=[a11, a12, a13],[a12, a22, a23],[a13, a23, a33]

        orientation_tensor=np.array(orientation_tensor)
        # calcul eigenvalue and eigenvector
        w,v=np.linalg.eig(orientation_tensor)
        
        #compute theta and phi
        theta=np.arccos(zc)
        phi=np.arctan2(yc, xc)
        # caculate coordinate for the pole figure
        xx = np.multiply(2*np.sin(theta/2),np.cos(phi))
        yy = np.multiply(2*np.sin(theta/2),np.sin(phi))
        
        if allpixel:
            rand=np.arange(np.size(xx))
        else:
            # select only 10000 pixels
            rand=np.int32(np.linspace(1., np.size(xc)-1, np.size(xc)/1000))
            
        # select phi[rand] is not an NaN value
        rand=rand[~np.isnan(np.reshape(xx[rand],np.size(rand)))]
                      
        # plot pixel orientation with density color bar
        x=np.reshape(xx[rand],np.size(rand))
        y=np.reshape(yy[rand],np.size(rand))
        xy = np.vstack([x,y])
        z = gaussian_kde(xy)(xy)
        
        idf=np.where(z>np.percentile(z, filter))
        x=x[idf]
        y=y[idf]
        z=z[idf]
        
        plt.scatter(x, y, c=z, s=20, edgecolor='')
        plt.colorbar(orientation='vertical',aspect=4,shrink=0.5)
        # compute a circle
        omega = np.linspace(0, 2*math.pi, 60)
        x_circle = 1.5*np.cos(omega)
        y_circle = 1.5*np.sin(omega)
        plt.plot(x_circle, y_circle,'k', linewidth=3)
        # draw a cross for x and y directiondef new_ori_TJ(self,mask):
        plt.plot([1.5, 0],[0, 1.5],'+k',markersize=12)
        # write axis
        plt.text(1.6, -0.04, r'X')
        plt.text(-0.04, 1.6, r'Y')
        plt.text(-1.4, 1.4, r'[0001]')
        
        # plot eigenvector
        #compute theta_e and phi_e
        if peigen:
            # to plot the pole figure here zc should be positive
            for i in list(xrange(3)):
                #test if zc is negative
                if np.sum(v[2,i])<0:
                    # replace the vector by -vector
                    v[:,i]=-v[:,i]
            theta_e=np.arccos(v[2,:])
            phi_e=np.arctan2(v[1,:], v[0,:])
            # caculate coordinate for the pole figure
            xx_e = np.multiply(2*np.sin(theta_e/2),np.cos(phi_e))
            yy_e = np.multiply(2*np.sin(theta_e/2),np.sin(phi_e))
            plt.plot(xx_e,yy_e,'sk',markersize=8)
            # write eigenvalue        
            plt.text(xx_e[0]+0.04, yy_e[0]+0.04,str(round(w[0],2)))
            plt.text(xx_e[1]+0.04, yy_e[1]+0.04,str(round(w[1],2)))
            plt.text(xx_e[2]+0.04, yy_e[2]+0.04,str(round(w[2],2)))
        # figure format
        plt.axis("equal")
        plt.axis('off')
        
        return w
    
    def grain_ori(self):
        '''
        Give the grain orientation output
        '''
        plt.imshow(self.grains.field,aspect='equal')
        plt.waitforbuttonpress()
        print('midle mouse clic when you are finish')
        #grain wanted for the plot
        id=np.int32(np.array(pylab.ginput(0)))
        plt.close('all')
        
        phi=self.phi.field[id[:,1],id[:,0]]
        phi1=self.phi1.field[id[:,1],id[:,0]]
        
        return [phi1,phi]
        
    def plot(self,nlut=512):
        '''
        Plot the data using a 2d lut
        
        :param nlut: number of pixel tou want for the 2d LUT (default 512)
        :type nlut: int
        :return: figure of orientation mapping
        :rtype: matplotlib figure
        :Exemple: 
            >>> data.plot()
            >>> plt.show()
            >>> # print the associated color wheel
            >>> lut=lut()
            >>> plt.show()
            
        .. note:: It takes time to build the colormap
        '''
        # size of the map
        nx=np.shape(self.phi.field)
        # create image for color map
        img=np.ones([nx[0],nx[1],3])
        # load the colorwheel
        rlut=lut(nx=nlut,circle=False)
        # fill the color map
        XX=(nlut-1)/2*np.multiply(np.sin(self.phi.field),np.cos(self.phi1.field))+(nlut-1)/2
        YY=(nlut-1)/2*np.multiply(np.sin(self.phi.field),np.sin(self.phi1.field))+(nlut-1)/2
    
        for i in list(xrange(nx[0])):
            for j in list(xrange(nx[1])):
                if ~np.isnan(self.phi.field[i,j]):
                    img[i,j,0]=rlut[np.int32(XX[i,j]),np.int32(YY[i,j]),0]
                    img[i,j,1]=rlut[np.int32(XX[i,j]),np.int32(YY[i,j]),1]
                    img[i,j,2]=rlut[np.int32(XX[i,j]),np.int32(YY[i,j]),2]
                
        h=plt.imshow(img,extent=(0,nx[1]*self.phi.res,0,nx[0]*self.phi.res))               
        
        return h,img
    

    def misorientation_profile(self, plot='all',orientation=False,pos=0):       
        '''
        Compute the misorientation profile along a line
        
        :param plot: option for to misorientation profile plot, 'all' (default), 'mis2o', 'mis2p'
        :type plot: str
        :param orientation: option for the color code used for the map, False (default) use phi1 and True use colorwheel (take time)
        :type orientation: bool
        :param pos: coordinate of the profile line - 0 (default) click on the map to select the 2 points
        :type pos: array
        :return: x - coordinate along the line
        :rtype: array, float
        :return: mis2o,mis2p - misorientation angle to the origin, and misorientation angle to the previous pixel
        :rtype: array, float
        :return: h - matplotlib image with line draw on the orientation map, subplot with mis2o and/or mis2p profile
        :return: pos - coordinate of the profile line
        :Exemple: 
            >>> [x,mis2o,mis2p,h,pos]=data.misorientation_profile()
            >>> rpos = pos[::-1]
            >>> [x,mis2o,mis2p,hr,pos]=data.misorientation_profile(pos=rpos)
            >>> plt.show()
        '''
        
        # size of the map
        ss=np.shape(self.phi1.field)
        # plot the data with phi1 value
        if np.size(pos)==1:
            h=plt.figure()
            self.phi1.plot()
            # select initial and final points for the line
            print('Select initial and final points for the line :')
            pos=np.array(pylab.ginput(2))
            plt.close(h)
        
        yy=np.float32([pos[0][0],pos[1][0]])/self.phi.res
        xx=np.float32([pos[0][1],pos[1][1]])/self.phi.res
        
        # numbers of pixel along the line
        nb_pixel=np.int32(np.sqrt((xx[1]-xx[0])**2+(yy[1]-yy[0])**2))
        
        # calcul for each pixel
        phi=[]
        phi1=[]
        x=[]
        xi=[]
        yi=[]
        mis2p=[]
        mis2o=[]
        ori=[]
        for i in list(xrange(nb_pixel)):
            # find the coordinate x an y along the line
            xi.append(ss[0]-np.int32(np.round(i*(xx[1]-xx[0])/nb_pixel+xx[0])))
            yi.append(np.int32(np.round(i*(yy[1]-yy[0])/nb_pixel+yy[0])))
            # extract phi and phi1
            phi.append(self.phi.field[xi[i],yi[i]])
            phi1.append(self.phi1.field[xi[i],yi[i]])
            
            # ori0 and orii are the c axis vector
            ori.append(np.mat([np.cos(np.mod(phi1[i]-math.pi/2,2*math.pi))*np.sin(phi[i]) , np.sin(np.mod(phi1[i]-math.pi/2,2*math.pi))*np.sin(phi[i]) ,np.cos(phi[i])]))   
            # mis2o is the misorientation between pixel i and the origin
            mis2o.append(np.float(np.arccos(np.abs(ori[0]*np.transpose(ori[i])))*180/math.pi))
            if i>0:
            # mis2p is the misorientation to the previous pixel    
                mis2p.append(np.float(np.arccos(np.abs(ori[i]*np.transpose(ori[i-1])))*180/math.pi))
            # x is the position along the line
                x.append(np.sqrt((xi[i]-xi[0])**2+(yi[i]-yi[0])**2))
            else:
                mis2p.append(0.0)
                x.append(0.0)


        hh=plt.figure()
        plt.subplot(211)
        if orientation:
            self.plot()
        else:
            self.phi1.plot()
        plt.hold('on')
        plt.plot(yy*self.phi.res,xx*self.phi.res)
        # plot misorientation profile
        plt.subplot(212)
        if plot=='all' or plot=='mis2o':
            plt.plot(x,mis2o,'-b')
        if plot=='all' or plot=='mis2p':
            plt.plot(x,mis2p,'-k')    
        plt.grid(True)
            
        return x, mis2o, mis2p, hh, pos
    
    
    def addgrain(self,ori=0):
        '''
        add a grain inside the microstructure
        
        :param ori: orienation of the new grain [phi1 phi] (default random value)
        :type ori: array, float
        :return: new_micro, object with the new grain include
        :rtype: aita
        :Exemple: 
            >>> data.addgrain()      
        '''
        
        # select the contour of the grains
        h=self.grains.plot()
        # click on the submit of the new grain
        plt.waitforbuttonpress()
        print('click on the submit of the new grain :')
        x=np.array(pylab.ginput(3))/self.grains.res
        plt.close('all')
        
        # select a subarea contening the triangle
        minx=np.int(np.fix(np.min(x[:,0])))
        maxx=np.int(np.ceil(np.max(x[:,0])))
        miny=np.int(np.fix(np.min(x[:,1])))
        maxy=np.int(np.ceil(np.max(x[:,1])))
        
        # write all point inside this area
        gpoint=[]
        for i in list(xrange(minx,maxx)):
            for j in list(xrange(miny,maxy)):
                gpoint.append([i,j])
        
    
        # test if the point is inside the triangle    
        gIn=[]
        for i in list(xrange(len(gpoint))):
            gIn.append(isInsideTriangle(gpoint[i],x[0,:],x[1,:],x[2,:]))

        gpointIn=np.array(gpoint)[np.array(gIn)]
        
        #transform in xIn and yIn, the coordinate of the map
        xIn=np.shape(self.grains.field)[0]-gpointIn[:,1]
        yIn=gpointIn[:,0]
               
        # add one grains
        self.grains.field[xIn,yIn]=np.nanmax(self.grains.field)+1
        # add the orientation of the grains
        if ori==0:
            self.phi1.field[xIn,yIn]=random.random()*2*math.pi
            self.phi.field[xIn,yIn]=random.random()*math.pi/2
        else:
            self.phi1.field[xIn,yIn]=ori[0]
            self.phi.field[xIn,yIn]=ori[1]
            
        return
    
    def new_ori_TJ(self,mask,mean=True):
        '''
        Extract orientation to compare with CraFT simulation
        '''
        ng=(self.grains*mask).field        
        res=[]
        con=True
        
        while con:
            gID=self.grains.mask_build()
            print('triple junction label')
            x=input()
            ng=(self.grains*gID).field
            ngmax=np.nanmax(ng)
            for i in list(xrange(np.int32(ngmax))):
                id=np.where(self.grains.field==i)
                if len(id[0])>0:
                    if mean:
                        pp=np.array([[id[0][0],id[1][0]]])
                        phi1,pos=self.phi1.extract_data(pos=pp)
                        phi,pos=self.phi.extract_data(pos=pp)
                        if ~np.isnan(phi1):
                            res.append([i,phi1,phi,float(x)])
                    else:
                        for j in list(xrange(len(id[0]))):
                            pp=np.array([[id[0][j],id[1][j]]])
                            phi1,pos=self.phi1.extract_data(pos=pp)
                            phi,pos=self.phi.extract_data(pos=pp)
                            if ~np.isnan(phi1):
                                res.append([i,phi1,phi,float(x)])
                            
            print('continue ? 0 no, 1 yes')
            con=input()
        
        return res
            
      
##########################################################################
###################### Function need for aita class  #####################
##########################################################################        
        
def cart2pol(x, y):
    '''
    Convert cartesien coordinate x,y into polar coordinate rho, theta
    
    :param x: x cartesian coordinate
    :param y: y cartesian coordinate
    :type x: float
    :type y: float
    :return: rho (radius), theta (angle)
    :rtype: float
    :Exemple: >>> rho,theta=cart2pol(x,y)
    '''
    # transform cartesien to polar coordinate
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return(rho, phi)


def lut(nx=512,circle=True):
    '''
    Create a 2D colorwheel
    
    :param nx: number of pixel for the colorwheel
    :param circle: do you want create a black circle around
    :type nx: int
    :type circle: bool
    :return: lut
    :rtype: array of size [nx,nx,3]
    :Exemple:
        >>> lut2d=lut()
        >>> plt.imshow(lut)
        >>> plt.show()
    '''
    x=np.linspace(-math.pi/2, math.pi/2, nx)
    y=np.linspace(-math.pi/2, math.pi/2, nx)
    xv, yv = np.meshgrid(x, y)
    rho,phi=cart2pol(xv, yv)
    h = (phi-np.min(phi))/(np.max(phi)-np.min(phi))
    #print(h)
    v = rho/np.max(rho)
    # lut=[h,s,v]
    # colorwheel hsv
    luthsv = np.ones((nx, nx,3))
    luthsv[:,:,0]=h
    luthsv[:,:,2]=v
    # colorwheel rgb
    lutrgb = np.ones((nx, nx,3))
    for i in list(xrange(nx)):
        for j in list(xrange(nx)):
            lutrgb[i,j,0],lutrgb[i,j,1],lutrgb[i,j,2]=colorsys.hsv_to_rgb(luthsv[i,j,0],luthsv[i,j,1],luthsv[i,j,2])

        
    # build a circle color bar        
    if circle:
        for i in list(xrange(nx)):
            for j in list(xrange(nx)):
                if ((i-nx/2)**2+(j-nx/2)**2)**0.5>(nx/2):
                    lutrgb[i,j,0]=0 
                    lutrgb[i,j,1]=0
                    lutrgb[i,j,2]=0
                    


    return lutrgb
    
    
def isInsideTriangle(P,p1,p2,p3): #is P inside triangle made by p1,p2,p3?
    '''
    test if P is inside the triangle define by p1 p2 p3
    
    :param P: point you want test
    :param p1: one submit of the triangle
    :param p2: one submit of the triangle
    :param p3: one submit of the triangle
    :type P: array
    :type p1: array
    :type p2: array
    :type p3: array
    :return: isIn
    :rtype: bool
    :Exemple:
        >>> isInsideTriangle([0,0],[-1,0],[0,1],[1,0])
        >>> isInsideTriangle([0,-0.1],[-1,0],[0,1],[1,0])
    '''
    x,x1,x2,x3 = P[0],p1[0],p2[0],p3[0]
    y,y1,y2,y3 = P[1],p1[1],p2[1],p3[1]
    full = abs (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    first = abs (x1 * (y2 - y) + x2 * (y - y1) + x * (y1 - y2))
    second = abs (x1 * (y - y3) + x * (y3 - y1) + x3 * (y1 - y))
    third = abs (x * (y2 - y3) + x2 * (y3 - y) + x3 * (y - y2))
    return abs(first + second + third - full) < .0000001
