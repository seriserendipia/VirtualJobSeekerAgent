document.getElementById('btn').addEventListener('click', async () => {
  const res = await fetch('http://localhost:5000/', {
    method: 'GET',
    headers: {
      'X-From-Extension': 'true'
    }
  });
  console.log('fetch sent to backend');
  const text = await res.text();
  alert('Backend says: ' + text);
  console.log('Response from backend:', text);
});
