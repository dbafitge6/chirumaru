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

  const response = await fetch(
    `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${USERS_TABLE_ID}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AIRTABLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        fields: {
          Email: email,
          Password: hashedPassword,
          LoginMethod: loginMethod,
          CreatedAt: new Date().toISOString(),
        },
      }),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to create user');
  }

  return response.json();
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
