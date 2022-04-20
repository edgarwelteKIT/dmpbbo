# This file is part of DmpBbo, a set of libraries and programs for the 
# black-box optimization of dynamical movement primitives.
# Copyright (C) 2018 Freek Stulp
# 
# DmpBbo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# DmpBbo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with DmpBbo.  If not, see <http://www.gnu.org/licenses/>.

import os, sys
from abc import ABC, abstractmethod
import numpy as np
import warnings
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt                                               

lib_path = os.path.abspath('../../../python/')
sys.path.append(lib_path)

from functionapproximators.Parameterizable import Parameterizable
from functionapproximators.BasisFunction import *

class FunctionApproximator(Parameterizable):
    """Base class for all function approximators.

    See https://github.com/stulp/dmpbbo/blob/master/tutorial/functionapproximators.md
    """
        
    @abstractmethod
    def dim_input(self):
        pass
        
    @abstractmethod
    def train(self,inputs,targets):
        """Train the function approximator with input and target examples.
        
        Args:
            inputs (numpy.ndarray): Input values of the training examples.
            targets (numpy.ndarray): Target values of the training examples.
        """
        pass
    
    @abstractmethod
    def predict(self,inputs):
        """Query the function approximator to make a prediction.
        
        Args:
            inputs (numpy.ndarray): Input values of the query.
            
        Returns:
            numpy.ndarray: Predicted output values.
        """
        pass
    
    @abstractmethod
    def isTrained(self):
        """Determine whether the function approximator has already been trained with data or not.
        
        Returns:
            bool: True if the function approximator has already been trained, False otherwise.
        """
        pass

    def _getAxis(self,fig=None):
        if not fig:
            fig = plt.figure(figsize=(6,6))
        if self.dim_input()==1:
            return fig.add_subplot(111)
        elif self.dim_input()==2:
            return fig.add_subplot(111,projection='3d')
        else:
          raise ValueError('Cannot create axis with dim_input() = '+str(self.dim_input())+'.')

    @staticmethod
    def _getGrid(inputs_min,inputs_max,n_samples_per_dim=None):
        n_dims = inputs_min.size
        if n_dims==1:
            n_samples_per_dim = np.atleast_1d(101)
            inputs_grid = np.linspace(0.0, 2.0, n_samples_per_dim)
            
        elif n_dims==2:
            n_samples_per_dim = np.atleast_1d([21, 21])
            n_samples = np.prod(n_samples_per_dim)
            # Here comes naive inefficient implementation...
            x1s = np.linspace(-2.0, 2.0,n_samples_per_dim[0])
            x2s = np.linspace(-2.0, 2.0,n_samples_per_dim[1])
            inputs_grid = np.zeros((n_samples,n_dims))
            ii = 0
            for x1 in x1s:
                for x2 in x2s:
                    inputs_grid[ii,0] = x1
                    inputs_grid[ii,1] = x2
                    ii += 1
        else:
          raise ValueError('Cannot create axis with dim_input() = '+str(self.dim_input())+'.')
                    
        return (inputs_grid, n_samples_per_dim)                    

    @staticmethod
    def _plotGridValues(inputs,activations,ax,n_samples_per_dim):
        """Plot basis functions activations, whilst being smart about the dimensionality of input data."""
        
        n_dims = len(numpy.atleast_1d(inputs[0]))
        if (n_dims==1):
            lines = ax.plot(inputs,activations, '-')
            
        elif (n_dims==2):
            n_basis_functions = len(activations[0])
            basis_functions_to_plot = range(n_basis_functions)
            
            inputs_0_on_grid = numpy.reshape(inputs[:,0],n_samples_per_dim)
            inputs_1_on_grid = numpy.reshape(inputs[:,1],n_samples_per_dim)
            lines = [];
            values_range = numpy.amax(activations)-numpy.amin(activations)
            for i_basis_function in basis_functions_to_plot:
              #cur_color = colors[i_basis_function]
              cur_activations = activations[:,i_basis_function];
              # Make plotting easier by leaving out small numbers
              #cur_activations[numpy.abs(cur_activations)<values_range*0.001] = numpy.nan 
              activations_on_grid = numpy.reshape(cur_activations,n_samples_per_dim)
              cur_lines = ax.plot_wireframe(inputs_0_on_grid,inputs_1_on_grid,activations_on_grid,linewidth=0.5,rstride=1, cstride=1)
              lines.append(cur_lines) 
              
        else:
            print('Cannot plot input data with a dimensionality of '+str(n_dims)+'.')
            lines = []
            
        return lines
        
    def plotBasisFunctions(self,inputs_min,inputs_max,**kwargs):
        ax = kwargs.get('ax') or self._getAxis()
        
        inputs, n_samples_per_dim = FunctionApproximator._getGrid(inputs_min,inputs_max)
        activations = self.getActivations(inputs)
        
        lines = self._plotGridValues(inputs, activations, ax, n_samples_per_dim)
        alpha = 1.0 if len(n_samples_per_dim)<2 else 0.3
        plt.setp(lines, color=[0.7,0.7,0.7], linewidth=1,alpha=alpha)
        
    def plotPredictionsGrid(self,inputs_min,inputs_max,**kwargs):
        ax = kwargs.get('ax') or self._getAxis()
        
        inputs, n_samples_per_dim = FunctionApproximator._getGrid(inputs_min,inputs_max)
        outputs = self.predict(inputs)
              
        if (self.dim_input()==1):
            h = ax.plot(inputs,outputs,'-')
        elif (self.dim_input()==2):
            inputs_0_on_grid = np.reshape(inputs[:,0],n_samples_per_dim)
            inputs_1_on_grid = np.reshape(inputs[:,1],n_samples_per_dim)
            outputs_on_grid = np.reshape(outputs,n_samples_per_dim)
            h = ax.plot_wireframe(inputs_0_on_grid,inputs_1_on_grid,outputs_on_grid,rstride=1, cstride=1)
        else:
            print('Cannot plot input data with a dimensionality of '+str(self.dim_input())+'.')
            
        plt.setp(h, linewidth=1, color=[0.3,0.3,0.9],alpha=0.5)
    
        return h
        
    def plotPredictions(self,inputs,**kwargs):
        targets = kwargs.get('targets', [])
        ax = kwargs.get('ax') or self._getAxis()
        plot_residuals = kwargs.get('plot_residuals', False)
    
        outputs = self.predict(inputs)
        
        h_residuals = []
        if (self.dim_input()==1):
            if len(targets)>0:
                h_targets = ax.plot(inputs,targets,'o')
                if plot_residuals:
                    for ii in range(len(inputs)):
                        x = [inputs[ii], inputs[ii]]
                        y = [targets[ii], outputs[ii] ]
                        h = ax.plot(x,y,'-')
                        h_residuals.append(h)
            h_outputs = ax.plot(inputs,outputs,'o')
            
        elif (self.dim_input()==2):
            if len(targets)>0:
                h_targets = ax.plot(inputs[:,0],inputs[:,1],targets,'o')
                if plot_residuals:
                    for ii in range(len(inputs)):
                        x0 = [inputs[ii,0], inputs[ii,0]]
                        x1 = [inputs[ii,1], inputs[ii,1]]
                        y = [targets[ii], outputs[ii] ]
                        h = ax.plot(x0,x1,y,'-')
                        h_residuals.append(h)    
            h_outputs = ax.plot(inputs[:,0],inputs[:,1],outputs,'o')
            
        else:
            raise ValueError('Cannot plot input data with dim_input() = '+str(self.dim_input()))

        plt.setp(h_targets, markeredgecolor=None, markerfacecolor=[0.7,0.7,0.7], markersize=8)
        plt.setp(h_outputs, markeredgecolor=None, markerfacecolor=[0.2,0.2,0.8], markersize=6)
        if len(targets)>0:
            plt.setp(h_residuals, color=[0.8,0.3,0.3], linewidth=2)
        

    def plot(self,inputs,**kwargs):
        ax = kwargs.get('ax') or self._getAxis()
        targets = kwargs.get('targets', [])
        plot_residuals = kwargs.get('plot_residuals', False)
        
        inputs_min = np.min(inputs,axis=0)
        inputs_max = np.max(inputs,axis=0)
        self.plotBasisFunctions(inputs_min,inputs_max,ax=ax)
        self.plotPredictionsGrid(inputs_min,inputs_max,ax=ax)
        self.plotPredictions(inputs,targets=targets,ax=ax,plot_residuals=plot_residuals)
        

    def setSelectedParameters(self,selected_param_labels):
        selectable_param_labels = self.getSelectableParameters()
        self._selected_param_labels = []
        if isinstance(selected_param_labels,str):
            # Make sure it is a list
            selected_param_labels = [selected_param_labels]
        for label in selected_param_labels:
            if not label in selectable_param_labels:
                warnings.warn(label+" not in ["+', '.join(selectable_param_labels)+']: Ignoring')
            else:
                self._selected_param_labels.append(label)
                
    def getParameterVectorSelected(self):
        if not self.isTrained():
            raise ValueError('FunctionApproximator is not trained.')
            
        values = []
        for label in self._selected_param_labels:
            values.extend(self._model_params[label].flatten())
        return np.asarray(values)
            
    def setParameterVectorSelected(self,values):
        if not self.isTrained():
            raise ValueError('FunctionApproximator is not trained.')
            
        if len(values)!=self.getParameterVectorSelectedSize():
            raise ValueError(f'values ({len(values)}) should have same size as size of selected parameters vector ({self.getParameterVectorSelectedSize()})')
            
        offset = 0
        for label in self._selected_param_labels:
            expected_shape = self._model_params[label].shape
            cur_n_values = np.prod(expected_shape)
            cur_values = values[offset:offset+cur_n_values]
            self._model_params[label] = np.reshape(cur_values,expected_shape)
            offset += cur_n_values
            
    def getParameterVectorSelectedSize(self):
        size = 0
        for label in self._selected_param_labels:
            if label in self._model_params:
                size += np.prod(self._model_params[label].shape)
        return size