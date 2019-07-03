import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import animation
# from graph_utils import *
import time
# %matplotlib inline
import time

fig_size = 8
p,ax = plt.subplots(figsize=(fig_size,fig_size))

def rho_h(z,h=0.2):
    if (0 <= z and z < h):
        return 1
    if (h <= z and z <= 1):
        return (1/2)*(1+np.cos(np.pi*(z-h)/(1-h)))
    else:
        return 0

class Flock:
    """Implements the flocking framework as proposed in
    [3] R. Olfati-Saber, "Flocking for multi-agent dynamic systems:
    algorithms and theory," in IEEE Transactions on Automatic Control,
    vol. 51, no. 3, pp. 401-420, March 2006. doi: 10.1109/TAC.2005.864190"""
    def __init__(self,
                 acceleration=None,
                 acceleration_args=None,
                 inter_agent_distance=7,
                 communication_range=None,
                 number_of_agents=50,
                 initial_position=None,
                 initial_velocity=None,
                 time_step=0.01,
                 sigma_norm_epsilon = 0.1,
                 phi_a=5,
                 phi_b=5,
                 bump_function=None,
                 gamma_agent=False,
                 gamma_agent_Cq=1,
                 gamma_agent_Cp=1
                 ):
        self.N = number_of_agents
        if(isinstance(initial_position,type(np.ones(1)))):
            self.Q = initial_position
        elif(initial_position==None):
            self.Q = np.sqrt(25)*np.random.randn(self.N,2)
        if(isinstance(initial_velocity,type(np.ones(1)))):
            self.P = initial_velocity
        elif(initial_velocity==None):
            self.P = (10)*np.random.rand(self.N,2)-1
        self.gamma_agent=gamma_agent
        # 设置导航agent
        if(gamma_agent):
            # self.p = (10)*np.random.rand(1,2)-1
            # self.q = np.sqrt(50)*np.random.randn(1,2)
            self.p = np.array([2, 0])
            self.q = np.array([100, 0])
            self.C_q = gamma_agent_Cq
            self.C_p = gamma_agent_Cp

        if(callable(acceleration)):
            self.P_dot = acceleration
            if(acceleration_args != None):
                if(len(acceleration_args)==1):
                    self.args = (acceleration_args,1)
                else:
                    self.args = acceleration_args

        self.dt = time_step
        # gets the neighbour graph: edge if ||q_j-q_i||<r
        self.e = sigma_norm_epsilon
        self.d = inter_agent_distance
        self.a = phi_a
        self.b = phi_b
        if(communication_range==None):
            self.r = 1.2*self.d
        else:
            self.r = communication_range

        if(bump_function==None):
            self.rho_h = rho_h
        elif(callable(bump_function)):
            self.rho_h = rho_h
        else:
            print("Argument Error: bump_function must be a function")

        self.G = self.get_net(self.Q)

    def run_sim(self,T=10,save_data=False,to_agreement=False):
        if(save_data):
            self.Q_sim = []
            self.P_sim = []
            self.sim_time = []
            if(self.gamma_agent):
                self.p_sim = []
                self.q_sim = []
        t=0
        start = time.time()
        while t<T:
            self.G = self.get_net(self.Q)
            Q = self.Q.copy()
            P = self.P.copy()
            # 短时间内是匀速直线运动
            # 所以瞬时情况满足以下公式：s = vt ； v = at
            self.Q = self.Q+self.P*self.dt
            self.P = self.P+self.P_dot(Q,P)*self.dt
            if(self.gamma_agent):
                self.P = self.P+self.f_gamma(Q,P)*self.dt
                self.q = self.q + self.p*self.dt
            if(save_data):
                self.sim_time.append(time.time()-start)
                self.Q_sim.append(self.Q)
                self.P_sim.append(self.P)
                if(self.gamma_agent):
                    self.p_sim.append(self.p)
                    self.q_sim.append(self.q)
            if(to_agreement and self.velocity_angle_agreement(self.P)):
                t = T
            elif (to_agreement):
                t = t+self.dt
                T = T+self.dt
            else:
                t = t+self.dt

    def plot(self,
             Graph=True,
             fig_size=8,
             with_labels=False,
             node_size=25,
             width=2.5,
             arrow_width=.25):
        if(Graph):
            p = plt.figure(figsize=(fig_size,fig_size))
            unit = np.zeros(self.P.shape)
            norms = np.zeros(self.N)
            # 速度矢量归一化
            for i in range(0,self.N):
                norms[i] = np.linalg.norm(self.P[i])
                unit[i] = self.P[i]/norms[i]
            rel = np.zeros(self.P.shape)
            # 速度箭头矢量的归一化表示 用来后面表示arrow的长度
            for i in range(0,self.N):
                rel[i] = unit[i]*(np.linalg.norm(self.P[i])/max(norms))

            for i in range(0,self.N):
                plt.arrow(self.Q[i,0],self.Q[i,1],rel[i,0],rel[i,1],
                          width=arrow_width,
                          edgecolor='green',
                          facecolor='green')
            G = self.G.copy()
            Q = self.Q.copy()
            node_colors = ['red']

            if(self.gamma_agent):
                rel_gamma = self.p/max(norms)
                plt.arrow(self.q[0,0],self.q[0,1],rel_gamma[0,0],rel_gamma[0,1],
                          width=arrow_width,
                          edgecolor='blue',
                          facecolor='blue')
                G.add_node(self.N)
                node_colors = []
                for node in G:
                    if node < self.N:
                        node_colors.append('red')
                    if node == self.N:
                        node_colors.append('orange')
                Q = np.append(Q,self.q).reshape(self.N+1,2)

            nx.draw_networkx(G,
                             pos=Q,
                             node_color=node_colors,
                             edge_color='black',
                             width=width,
                             node_size=node_size,
                             with_labels=with_labels)
            plt.autoscale(enable=True)
            plt.xlim(plt.xlim()[0] - np.abs(unit[0, 0]), plt.xlim()[1] + np.abs(unit[0, 0]))
            plt.ylim(plt.ylim()[0] - np.abs(unit[0, 1]), plt.ylim()[1] + np.abs(unit[0, 1]))
            return p
        else:
            p = plt.figure(figsize=(fig_size,fig_size))
            plt.scatter(self.Q[:,0],self.Q[:,1])
            print('yinyinyin')
            return p

    def plot_time_series(self,
                         time_step_plot,
                         with_labels=False,
                         # fig_size=8,
                         node_size=25,
                         width=2.5,
                         arrow_width=.25):

        # p = plt.figure(figsize=(fig_size,fig_size))
        ax.clear()
        unit = np.zeros(self.P_sim[time_step_plot].shape)
        norms = np.zeros(self.N)
        # 速度矢量归一化
        for i in range(0,self.N):
            norms[i] = np.linalg.norm(self.P_sim[time_step_plot][i])
            unit[i] = self.P_sim[time_step_plot][i]/norms[i]
        rel = np.zeros(self.P_sim[time_step_plot].shape)
        # 速度箭头矢量的归一化表示 用来后面表示arrow的长度
        for i in range(0,self.N):
            rel[i] = unit[i]*(np.linalg.norm(self.P_sim[time_step_plot][i])/max(norms))

        for i in range(0,self.N):
            plt.arrow(self.Q_sim[time_step_plot][i,0],self.Q_sim[time_step_plot][i,1],rel[i,0],rel[i,1],
                      width=arrow_width,
                      edgecolor='green',
                      facecolor='green')
        self.G = self.get_net(self.Q_sim[time_step_plot])
        G = self.G.copy()
        Q = self.Q_sim[time_step_plot].copy()
        node_colors = ['red']

        if(self.gamma_agent):
            rel_gamma = self.p_sim[time_step_plot]/max(norms)
            # print(self.q_sim[time_step_plot][0,0],self.q_sim[time_step_plot][0,1],rel_gamma[0,0],rel_gamma[0,1])
            plt.arrow(self.q_sim[time_step_plot][0],self.q_sim[time_step_plot][1],rel_gamma[0],rel_gamma[1],
                      width=arrow_width,
                      edgecolor='blue',
                      facecolor='blue')
            G.add_node(self.N)
            node_colors = []
            for node in G:
                if node < self.N:
                    node_colors.append('red')
                if node == self.N:
                    node_colors.append('orange')
            Q = np.append(Q,self.q_sim[time_step_plot]).reshape(self.N+1,2)

        nx.draw_networkx(G,
                         pos=Q,
                         node_color=node_colors,
                         edge_color='black',
                         width=width,
                         node_size=node_size,
                         with_labels=with_labels)
        plt.autoscale(enable=True)
        plt.xlim(plt.xlim()[0] - np.abs(unit[0, 0]), plt.xlim()[1] + np.abs(unit[0, 0]))
        plt.ylim(plt.ylim()[0] - np.abs(unit[0, 1]), plt.ylim()[1] + np.abs(unit[0, 1]))
        plt.title("t = %ss" %(time_step_plot/100), fontsize=25)
        # return p

    def get_net(self,Q):
        """Draw a graph based on a position matrix with dimension Nxd"""
        G = nx.Graph()
        for i in range(0,self.N):
            for j in range(0,self.N):
                if (np.linalg.norm(Q[i,:]-Q[j,:])<self.r):
                    if(not G.has_edge(i,j)):
                        G.add_edge(i,j)
        return(G)

    def P_dot(self,Q,P):
        """For Flock class mostly"""
        u = np.zeros((self.N,2))
        A = self.get_spatial_adjacency(Q)
        for i in self.G.nodes():
            for j in self.G.neighbors(i):
                u[i] = u[i] + self.phi_alpha(self.sigma_norm(Q[j,:]-Q[i,:]))*(self.sigma_grad(Q[j,:]-Q[i,:]))
                u[i] = u[i] + A[i,j]*(P[j,:]-P[i,:])
        return u

    def get_spatial_adjacency(self,Q):
        r_alpha = self.sigma_norm(self.r)
        A = np.zeros((self.N,self.N))
        for i in range(0,self.N):
            for j in range(0,self.N):
                if (i != j):
                    A[i,j] = self.rho_h(self.sigma_norm(Q[j]-Q[i])/r_alpha)
        return A


    def sigma_norm(self,z):
        return (1/self.e)*(np.sqrt(1+self.e*(np.linalg.norm(z))**2)-1)

    def sigma_grad(self,z):
        return z/(1+self.e*self.sigma_norm(z))

    def sigma_1(self,z):
        return z/(np.sqrt(1+z**2))

    def phi(self,z):
        c = np.abs(self.a-self.b)/(np.sqrt(4*self.a*self.b))
        return (1/2)*((self.a+self.b)*self.sigma_1(z+c)+(self.a-self.b))

    def phi_alpha(self,z):
        r_alpha = self.sigma_norm(self.r)
        d_alpha = self.sigma_norm(self.d)
        return self.rho_h(z/r_alpha)*self.phi(z-d_alpha)

    def f_gamma(self,Q,P):
        return -self.C_q*(Q-self.q)-self.C_p*(P-self.p)

    def velocity_angle_agreement(self,v,tol=1e-6):
        unit = np.zeros(v.shape)
        for i in range(0,len(v)):
            unit[i] = v[i]/np.linalg.norm(v[i])
        ref = np.angle(complex(unit[1,0],unit[1,1]))
        for i in range(0,len(unit)):
            if (np.abs(ref - np.angle(complex(unit[i,0],unit[i,1])))>tol):
                return False
        return True

    def speed_agreement(self,v,tol=1e-6):
        for i in range(0,len(v)):
            if np.linalg.norm(v[1]-v[i])>tol:
                return False
        return True

def main():
    # could also leave Q and P for a default random initialisation
    N = 10
    Q = np.sqrt(2500) * np.random.randn(N, 2)
    P = (5) * np.random.rand(N, 2) - 1

    FS = Flock(number_of_agents=N,
               initial_position=Q,
               initial_velocity=P,
               inter_agent_distance=7,
               gamma_agent=True)

    # p = FS.plot(arrow_width=0.25)
    # plt.title("Initial state for flock following F2", fontsize=25)
    time_period = 10
    time_frames = time_period / 0.01
    FS.run_sim(T=time_period, save_data=True)
    ani = animation.FuncAnimation(p, FS.plot_time_series, int(time_frames),interval=1)
    plt.show()
    print('simlate for T=5 ends!')



if __name__ == "__main__":
    main()