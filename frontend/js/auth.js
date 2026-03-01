// Authentication state management
const Auth = (() => {
  const TOKEN_KEY = 'mp_token';
  const USER_KEY  = 'mp_user';

  return {
    getToken()       { return localStorage.getItem(TOKEN_KEY); },
    setToken(t)      { localStorage.setItem(TOKEN_KEY, t); },
    removeToken()    { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); },
    isLoggedIn()     { return !!localStorage.getItem(TOKEN_KEY); },

    getUser()        { try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; } },
    setUser(u)       { localStorage.setItem(USER_KEY, JSON.stringify(u)); },

    async login(email, password) {
      const data = await API.auth.login(email, password);
      this.setToken(data.access_token);
      const user = await API.auth.me();
      this.setUser(user);
      return user;
    },

    logout() {
      this.removeToken();
      App.navigateTo('login');
    },
  };
})();
