const useRefresh = () => {
    const refreshPage = () => {
      window.location.replace('/'); // Полная перезагрузка страницы
    };
  
    return refreshPage;
  };
  
  export default useRefresh;