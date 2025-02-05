#!/usr/bin/env python3

import math

import cherry as ch
import torch
from torch import nn
from torch.distributions import Normal, Categorical

EPSILON = 1e-6


def linear_init(module):
    if isinstance(module, nn.Linear):
        nn.init.xavier_uniform_(module.weight)
        module.bias.data.zero_()
    return module


class CaviaDiagNormalPolicy(nn.Module):

    def __init__(self, input_size, output_size, hiddens=None, activation='relu', num_context_params=2, device='cpu'):
        super(CaviaDiagNormalPolicy, self).__init__()
        self.device = device
        if hiddens is None:
            hiddens = [100, 100]
        if activation == 'relu':
            activation = nn.ReLU
        elif activation == 'tanh':
            activation = nn.Tanh
        layers = [linear_init(nn.Linear(input_size+num_context_params, hiddens[0])), activation()]
        for i, o in zip(hiddens[:-1], hiddens[1:]):
            layers.append(linear_init(nn.Linear(i, o)))
            layers.append(activation())
        layers.append(linear_init(nn.Linear(hiddens[-1], output_size)))

        self.num_context_params = num_context_params
        self.context_params = torch.zeros(self.num_context_params, requires_grad=True).to(self.device)

        self.mean = nn.Sequential(*layers).to(self.device)
        self.sigma = nn.Parameter(torch.Tensor(output_size)).to(self.device)
        self.sigma.data.fill_(math.log(1))

    def density(self, state):
        state = state.to(self.device, non_blocking=True)
        # concatenate context parameters to input
        state = torch.cat((state, self.context_params.expand(state.shape[:-1] + self.context_params.shape)),
                          dim=len(state.shape) - 1)

        loc = self.mean(state)
        scale = torch.exp(torch.clamp(self.sigma, min=math.log(EPSILON)))
        return Normal(loc=loc, scale=scale)

    def log_prob(self, state, action):
        density = self.density(state)
        return density.log_prob(action).mean(dim=1, keepdim=True)

    def forward(self, state):

        density = self.density(state)
        action = density.sample()
        return action

    def reset_context(self):
        self.context_params[:] = 0  # torch.zeros(self.num_context_params, requires_grad=True).to(self.device)


class DiagNormalPolicy(nn.Module):

    def __init__(self, input_size, output_size, hiddens=None, activation='relu', device='cpu'):
        super(DiagNormalPolicy, self).__init__()
        self.device = device
        if hiddens is None:
            hiddens = [100, 100]
        if activation == 'relu':
            activation = nn.ReLU
        elif activation == 'tanh':
            activation = nn.Tanh
        layers = [linear_init(nn.Linear(input_size, hiddens[0])), activation()]
        for i, o in zip(hiddens[:-1], hiddens[1:]):
            layers.append(linear_init(nn.Linear(i, o)))
            layers.append(activation())
        layers.append(linear_init(nn.Linear(hiddens[-1], output_size)))
        self.mean = nn.Sequential(*layers)
        self.sigma = nn.Parameter(torch.Tensor(output_size))
        self.sigma.data.fill_(math.log(1))
        
        #use this for getting the parameters for normalised observations and trajectories
    def prob_params(self, state):
        state = state.to(self.device, non_blocking=True)
        pi_mu = self.mean(state)
        std_dev = torch.exp(torch.clamp(self.sigma, min=math.log(EPSILON)))
        return pi_mu,std_dev
  
    def density(self, state):
        state = state.to(self.device, non_blocking=True)
        loc = self.mean(state)
        scale = torch.exp(torch.clamp(self.sigma, min=math.log(EPSILON)))
        return Normal(loc=loc, scale=scale)

    def log_prob(self, state, action):
        density = self.density(state)
        return density.log_prob(action).mean(dim=1, keepdim=True)

    def forward(self, state):
        density = self.density(state)
        action = density.sample()
        return action
        def forward(self, state):
        density = self.density(state)
        action = density.sample()
        log_prob = density.log_prob(action).mean().view(-1, 1).detach()
        return log_prob,action
    
    def set_params_1d(self, params):
        """Set params for ES (theta)
        """
        model = self.mean()
        n = model.parameters()
        idx = 0
        for e in n:
            e = params[idx:idx + e.size].reshape(e.shape).
            idx += e.size
            
    def get_params_1d(self):
        """Get params for ES (theta)
        """
        model = self.mean()
        n = model.parameters()
        return np.concatenate([torch.flatten(e.detach()) for e in n])



class CategoricalPolicy(nn.Module):

    def __init__(self, input_size, output_size, hiddens=None):
        super(CategoricalPolicy, self).__init__()
        if hiddens is None:
            hiddens = [100, 100]
        layers = [linear_init(nn.Linear(input_size, hiddens[0])), nn.ReLU()]
        for i, o in zip(hiddens[:-1], hiddens[1:]):
            layers.append(linear_init(nn.Linear(i, o)))
            layers.append(nn.ReLU())
        layers.append(linear_init(nn.Linear(hiddens[-1], output_size)))
        self.mean = nn.Sequential(*layers)
        self.input_size = input_size
        
        
    def prob_params(self, state):
        state = state.to(self.device, non_blocking=True)
        pi_mu = self.mean(state)
        return pi_mu

    
        #use this for getting the parameters for normalised observations and trajectories
    
    def density(self, state):
        state = ch.onehot(state, dim=self.input_size)
        loc = self.mean(state)
        density = Categorical(logits=loc)
        return density  
   
    def forward(self, state):
        density = self.density(state)
        action = density.sample()
        log_prob = density.log_prob(action).mean().view(-1, 1).detach()
        return log_prob,action
    
    def set_params_1d(self, params):
        """Set params for ES (theta)
        """
        model = self.mean()
        n = model.parameters()
        idx = 0
        for e in n:
            temp = params[idx:idx + e.size].reshape(e.shape)
            e = temp.detach()
            idx += e.size

    def get_params_1d(self):
        """Get params for ES (theta)
        """
        model = self.mean()
        n = model.parameters()
        return np.concatenate([torch.flatten(e.detach()) for e in n])
  #use .forward for log_prob 
        
        
        
