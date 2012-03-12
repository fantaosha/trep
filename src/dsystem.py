import trep
import numpy as np

# There is a lot of input validation here because I've dealt with a
# lot of headaches from mismatching array dimensions and shapes in the
# past.

class DSystem(object):
    """
    Wrapper to treat a trep variational integrator as an arbitrary
    discrete system with
      X[k+1] = f(X[k], U[k], k)
    where
      X[k] = [ Q[k] ; p[k] ; v[k] ]
         v[k] = (rho[k] - rho[k-1]) / (t[k]-t[k-1])         
      U[k] = [ u[k] ; rho[k+1] ]
    """
    # State is X[k] = [ Q[k] ; p[k] ; v[k] ]
    # Input is U[k] = [ u[k] ; rho[k+1] ]

    # You have to provide the time vector to the discrete system so it
    # can correctly calculate the vk[k] part of the state and provide
    # the time to the variational integrator while presenting the
    # f(x[k], u[k], k) interface.

    
    def __init__(self, varint, t):
        self.varint = varint

        self._xk = None
        self._uk = None
        self._time = np.array(t).squeeze()
        self._k = 0

        self._nQ = len(self.system.configs)
        self._np = len(self.system.dyn_configs)
        self._nv = len(self.system.kin_configs)
        self._nu = len(self.system.inputs)
        self._nrho = len(self.system.kin_configs)

        self._nX = self._nQ + self._np + self._nv
        self._nU = self._nu + self._nrho

        # Slices of the components in the appropriate vector
        self._slice_Q = slice(0, self._nQ)
        self._slice_p = slice(self._nQ, self._nQ + self._np)
        self._slice_v = slice(self._nQ + self._np, self._nX)
        self._slice_u = slice(0, self._nu)
        self._slice_rho = slice(self._nu, self._nU)

    @property
    def nX(self):
        """Number of states to the discrete system."""
        return self._nX
    
    @property
    def nU(self):
        """Number of inputs to the discrete system."""
        return self._nU

    @property
    def time(self):
        """The time of the discrete steps."""
        return self._time

    @property
    def system(self):
        """The mechanical system modeled by the variational integrator."""
        return self.varint.system

    @time.setter
    def time(self, t):
        t = np.array(t).squeeze()
        assert t.ndim == 1
        self._time = np.array(t).squeeze()

    def kf(self):
        """
        Return the last available state that the system can be set to.
        This is one less than the length of the time vector.
        """
        return len(self._time)-1


    def build_state(self, Q=None, p=None, v=None):
        """
        Build state vector from components.  Unspecified components
        are set to zero.
        """
        X = np.zeros((self._nX, ))

        if Q is not None: X[self._slice_Q] = Q
        if p is not None: X[self._slice_p] = p
        if v is not None: X[self._slice_v] = v
        return X         

    def build_input(self, u=None, rho=None):
        """
        Build input vector from components.  Unspecified components
        are set to zero.
        """
        U = np.zeros((self._nU, ))

        if u is not None: U[self._slice_u] = u
        if rho is not None: U[self._slice_rho] = rho
        return U

    def build_trajectory(self, Q=None, p=None, v=None, u=None, rho=None):
        """
        Combine component trajectories into a state and input
        trajectories.  The state length is the same as the time base,
        the input length is one less than the time base.  Unspecified
        components are set to zero.

        dsys.build_trajectory() -> all zero state and input trajectories
        """

        def bad_arguments(self, reason):
            string = reason + "\n"
            string += "Arguments: \n"
            for name, value in [ ('Q',Q), ('p',p), ('v',v), ('u',u), ('rho', rho) ]:
                if value is None:
                    string += "  %s: None\n" % name
                else:
                    string += "  %s: %r, shape=%r\n" % (name, type(Q), np.array(value, copy=False).shape)
            raise StandardError(string)

        # Check the lengths for consistency
        if Q is not None and len(Q) != len(self._time):
            bad_arguments("Invalid length for Q (expected %d)" % len(self._time))
        if p is not None and len(p) != len(self._time):
            bad_arguments("Invalid length for p (expected %d)" % len(self._time))
        if v is not None and len(v) != len(self._time):
            bad_arguments("Invalid length for v (expected %d)" % len(self._time))
        if u is not None and len(u) != len(self._time)-1:
            bad_arguments("Invalid length for u (expected %d)" % (len(self._time)-1))
        if rho is not None and len(rho) != len(self._time)-1:
            bad_arguments("Invalid length for rho (expected %d)" % (len(self._time)-1))

        X = np.zeros((len(self._time), self._nX))
        U = np.zeros((len(self._time)-1, self._nU))
        if Q is not None: X[:,self._slice_Q] = Q
        if p is not None: X[:,self._slice_p] = p
        if v is not None: X[:,self._slice_v] = v
        if u is not None:   U[:,self._slice_u] = u
        if rho is not None: U[:,self._slice_rho] = rho
        
        return X,U
        
    def split_state(self, X=None):
        """
        Split a state vector into its configuration, moementum, and
        kinematic velocity parts.  If X is None, returns zeros arrays
        for each component.

        Returns (Q,p,v)
        """
        if X is None:
            X = nd.zeros(self.nX)
        Q = X[self._slice_Q]
        p = X[self._slice_p]
        v = X[self._slice_v]
        return (Q,p,v)

    def split_input(self, U=None):
        """
        Split a state input vector U into it's force and kinematic
        input parts, (u, rho).
        """
        if U is None:
            U = np.zeros(self.nU)
        u = U[self._slice_u]
        rho = U[self._slice_rho]
        return (u, rho)
        
    def split_trajectory(self, X=None, U=None):
        """
        Split an X,U state trajectory into its Q,p,v,u,rho components.
        If X or U are None, the corresponding components are arrays of
        zero..
        """
        if X is None and U is None:
            X = np.zeros((len(self._time), self.nX))
            U = np.zeros((len(self._time)-1, self.nU))            
        elif X is None:
            X = np.zeros((U.shape[0]+1, self.nX))
        elif U is None:
            U = np.zeros((X.shape[0]+1, self.nU))
            
        Q = X[:,self._slice_Q]
        p = X[:,self._slice_p]
        v = X[:,self._slice_v]
        u = U[:,self._slice_u]
        rho = U[:,self._slice_rho]
        return (Q,p,v,u,rho)

        
    def set(self, xk, uk, k, lambda_k=None):
        """
        Set the current state, input, and time of the discrete system.
        """
        self._k = k
        (q1, p1, v1) = self.split_state(xk)
        (u1, rho2) = self.split_input(uk)
        t1 = self._time[self._k+0]
        t2 = self._time[self._k+1]

        self.varint.initialize_from_state(t1, q1, p1, lambda_k)
        self.varint.step(t2, u1, rho2)

        
    def step(self, uk):
        """
        Advance the system to the next discrete time using the given
        values for the input.  Returns a numpy array.
        """
        self._k += 1
        (u1, rho2) = self.split_input(uk)
        t2 = self._time[self._k+1]
        self.varint.step(t2, u1, rho2)


    def f(self):
        """
        Get the new state of the system.
        """
        v2 = [(q2-q1)/(self.varint.t2 - self.varint.t1)
              for (q2, q1) in zip(self.varint.q2, self.varint.q1)]
        v2 = v2[len(self.system.dyn_configs):]
        return self.build_state(self.varint.q2, self.varint.p2, v2)


    def fdx(self):
        """
        Get the derivative of the f() with respect to the state.
        Returns a numpy array with derivatives across the rows.
        """
        
        # Initialize with diagonal matrix of -1/dt to get dv/dv block.
        # The other diagonal terms will be overwritten.
        dt = self._time[self._k+1] - self._time[self._k+0]
        fdx = np.diag(np.ones(self._nX) * -1.0/dt)
        fdx[self._slice_Q, self._slice_Q] = self.varint.q2_dq1()
        fdx[self._slice_Q, self._slice_p] = self.varint.q2_dp1()
        fdx[self._slice_p, self._slice_Q] = self.varint.p2_dq1()
        fdx[self._slice_p, self._slice_p] = self.varint.p2_dp1()
        return fdx


    def fdu(self):
        """
        Get the derivative of the f() with respect to the input.
        Returns a numpy array with derivatives across the rows.
        """
        
        dt = self._time[self._k+1] - self._time[self._k+0]
        fdu = np.zeros((self._nX, self._nU))
        fdu[self._slice_Q, self._slice_u] = self.varint.q2_du1()
        fdu[self._slice_Q, self._slice_rho] = self.varint.q2_dk2()
        fdu[self._slice_p, self._slice_u] = self.varint.p2_du1()
        fdu[self._slice_p, self._slice_rho] = self.varint.p2_dk2()
        fdu[self._slice_v, self._slice_rho] = np.diag(np.ones(self._nrho) * 1.0/dt)
        return fdu


    def fdxdx(self, z):
        """
        Get the second derivative of f with respect to the state, with
        the outputs multiplied by vector z.  Returns a [nX x nX] numpy
        array .
        """

        zQ = z[self._slice_Q]
        zp = z[self._slice_p]
        # Don't care about zv, because second derivative is always zero.

        fdxdx = np.zeros((self._nX, self._nX))
        fdxdx[self._slice_Q, self._slice_Q] = (np.inner(zQ, self.varint.q2_dq1dq1()) +
                                               np.inner(zp, self.varint.p2_dq1dq1()))            
        fdxdx[self._slice_Q, self._slice_p] = (np.inner(zQ, self.varint.q2_dq1dp1()) +
                                               np.inner(zp, self.varint.p2_dq1dp1()))
        fdxdx[self._slice_p, self._slice_Q] = fdxdx[self._slice_Q, self._slice_p].T

        fdxdx[self._slice_p, self._slice_p] = (np.inner(zQ, self.varint.q2_dp1dp1()) +
                                               np.inner(zp, self.varint.p2_dp1dp1()))
        return fdxdx

        
    def fdxdu(self, z):
        """
        Get the second derivative of f with respect to the state and
        input, with the outputs multiplied by vector z. Returns a [nX
        x nU] numpy array .
        """        

        zQ = z[self._slice_Q]
        zp = z[self._slice_p]
        # Don't care about zv, because second derivative is always
        # zero.

        fdxdu = np.zeros((self._nX, self._nU))
        fdxdu[self._slice_Q, self._slice_u]   = (np.inner(zQ, self.varint.q2_dq1du1()) +
                                                 np.inner(zp, self.varint.p2_dq1du1()))
        fdxdu[self._slice_Q, self._slice_rho] = (np.inner(zQ, self.varint.q2_dq1dk2()) +
                                                 np.inner(zp, self.varint.p2_dq1dk2()))
        fdxdu[self._slice_p, self._slice_u]   = (np.inner(zQ, self.varint.q2_dp1du1()) +
                                                 np.inner(zp, self.varint.p2_dp1du1()))
        fdxdu[self._slice_p, self._slice_rho] = (np.inner(zQ, self.varint.q2_dp1dk2()) +
                                                 np.inner(zp, self.varint.p2_dp1dk2()))
        return fdxdu


    def fdudu(self, z):
        """
        Get the second derivative of f with respect to the input, with
        the outputs multiplied by vector z.  Returns a [nU x nU] numpy
        array .
        """

        zQ = z[self._slice_Q]
        zp = z[self._slice_p]
        # Don't care about zv, because second derivative is always zero.

        fdudu = np.zeros((self._nU, self._nU))
        fdudu[self._slice_u, self._slice_u]   = (np.inner(zQ, self.varint.q2_du1du1()) +
                                                 np.inner(zp, self.varint.p2_du1du1()))
        fdudu[self._slice_u, self._slice_rho] = (np.inner(zQ, self.varint.q2_du1dk2()) +
                                                 np.inner(zp, self.varint.p2_du1dk2()))
        fdudu[self._slice_rho, self._slice_u]   = fdudu[self._slice_u, self._slice_rho].T
        fdudu[self._slice_rho, self._slice_rho] = (np.inner(zQ, self.varint.q2_dk2dk2()) +
                                                   np.inner(zp, self.varint.p2_dk2dk2()))
        return fdudu
    

    def validate_derivatives(self, xk, uk, k, delta=1e-5, tolerance=1e-5, verbose=False):

        self.set(xk, uk, k)
        f0 = self.f()
        fdx_exact = self.fdx()
        fdu_exact = self.fdu()

        # Build approximation for fdx and fdu
        fdx_approx = np.zeros((self.nX, self.nX))
        for i1 in range(self.nX):
            dxk = xk.copy()
            dxk[i1] += delta
            self.set(dxk, uk, k)
            dfp = self.f()
            dxk = xk.copy()
            dxk[i1] -= delta
            self.set(dxk, uk, k)
            dfm = self.f()
            fdx_approx[:, i1] = (dfp-dfm)/(2*delta)

        fdu_approx = np.zeros((self.nX, self.nU))
        for i1 in range(self.nU):
            duk = uk.copy()
            duk[i1] += delta
            self.set(xk, duk, k)
            dfp = self.f()
            duk = uk.copy()
            duk[i1] -= delta
            self.set(xk, duk, k)
            dfm = self.f()
            fdu_approx[:, i1] = (dfp-dfm)/(2*delta)
            
        fdx_error = np.linalg.norm(fdx_exact - fdx_approx)/np.linalg.norm(fdx_exact)
        fdu_error = np.linalg.norm(fdu_exact - fdu_approx)/np.linalg.norm(fdu_exact)
        return fdx_error, fdu_error


    def save_state_trajectory(self, filename, X, U):
        """
        Save a trajectory to a file.
        """
        (Q,p,v,u,rho) = self.split_trajectory(X,U)
        trep.save_trajectory(filename, self.system, self._time, Q, p, v, u, rho)


    def load_state_trajectory(self, filename):
        """
        Load a trajectory from a file.
        """
        (t,Q,p,v,u,rho) = trep.load_trajectory(filename, self.system)
        self.time = t
        return self.build_trajectory(Q,p,v,u,rho)


