import bcrypt from 'bcryptjs';

const AIRTABLE_BASE_ID = process.env.AIRTABLE_BASE_ID;
const AIRTABLE_API_KEY = process.env.AIRTABLE_API_KEY;
const USERS_TABLE_ID = 'tblyQa1XW4lMxmaLp';

export async function hashPassword(password: string) {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hashedPassword: string) {
  return bcrypt.compare(password, hashedPassword);
}

export async function createUser(email: string, password: string, loginMethod: 'Email' | 'Google') {
  const hashedPassword = loginMethod === 'Google' ? '' : await hashPassword(password);

  try {
    const response = await fetch('/api/auth/create-user', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password: hashedPassword,
        loginMethod,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('API error:', response.status, errorData);
      throw new Error(`Failed to create user: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
}

export async function getUserByEmail(email: string) {
  const response = await fetch(
    `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${USERS_TABLE_ID}`,
    {
      headers: {
        'Authorization': `Bearer ${AIRTABLE_API_KEY}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }

  const data = await response.json();
  return data.records.find((record: any) =>
    record.fields.Email === email
  );
}
