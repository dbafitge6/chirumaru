export async function POST(request: Request) {
  const { email, password, loginMethod } = await request.json();

  const AIRTABLE_BASE_ID = process.env.AIRTABLE_BASE_ID;
  const AIRTABLE_API_KEY = process.env.AIRTABLE_API_KEY;
  const STORES_TABLE_ID = 'tblcOdcqCxzb7kX0e';

  if (!AIRTABLE_BASE_ID || !AIRTABLE_API_KEY) {
    return Response.json(
      { error: 'Airtable credentials not configured' },
      { status: 500 }
    );
  }

  try {
    // Create user record in Stores table (for user tracking)
    const response = await fetch(
      `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${STORES_TABLE_ID}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${AIRTABLE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          records: [
            {
              fields: {
                'Store Name': email,
                '一言メモ': `[User Account] ${loginMethod} Login - ${new Date().toISOString()}`,
              },
            },
          ],
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Airtable API error:', response.status, errorData);
      return Response.json(
        { error: `Airtable API error: ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return Response.json(data, { status: 201 });
  } catch (error) {
    console.error('Error creating user record:', error);
    return Response.json(
      { error: 'Failed to create user record' },
      { status: 500 }
    );
  }
}
