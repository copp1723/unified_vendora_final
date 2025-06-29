const { PredictionServiceClient } = require('@google-cloud/aiplatform');

const client = new PredictionServiceClient();

async function makePrediction() {
  const project = 'vendora-464403'; // Your GCP project ID
  const location = 'us-central1';   // Replace if your endpoint is in a different region
  const endpointId = 'YOUR_ENDPOINT_ID_HERE'; // 🔁 Replace with your actual Vertex AI endpoint ID

  const endpoint = `projects/${project}/locations/${location}/endpoints/${endpointId}`;

  const request = {
    endpoint,
    instances: [ 
      { content: "your test input here" } // Replace with your actual input format
    ],
    parameters: {}, // Optional
  };

  const [response] = await client.predict(request);
  console.log('Prediction response:', JSON.stringify(response.predictions, null, 2));
}

makePrediction().catch(console.error);
