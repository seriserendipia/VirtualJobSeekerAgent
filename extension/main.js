document.getElementById('btn').addEventListener('click', async () => {
  const res = await fetch('http://localhost:5000/', {
    method: 'GET',
    headers: {
      'X-From-Extension': 'true'
    }
  });
  console.log('fetch sent to backend (GET /)');
  const text = await res.text();
  alert('Backend says: ' + text);
  console.log('Response from backend (GET /):', text);
});

// NEW: Event listener for sending email from file
document.getElementById('sendEmailFromFileBtn').addEventListener('click', async () => {
    alert('Attempting to send email using data from email_content.json...');
    try {
        const res = await fetch('http://localhost:5000/send-email-from-file', {
            method: 'GET', // As the backend is configured to read from file on GET
            headers: {
                // 'X-From-Extension': 'true' // Add this header if your /send-email-from-file route also requires it in server.py
            }
        });

        const responseText = await res.text();
        const responseJson = JSON.parse(responseText); // Parse JSON response

        if (res.ok) {
            alert('Email send triggered: ' + responseJson.message);
            console.log('Backend response (send-email-from-file):', responseJson);
        } else {
            alert('Failed to trigger email send: ' + (responseJson.error || responseJson.message));
            console.error('Backend error (send-email-from-file):', responseJson);
        }
    } catch (error) {
        console.error('Error sending email from file:', error);
        alert('Failed to connect to backend for sending email from file. Check console.');
    }
});