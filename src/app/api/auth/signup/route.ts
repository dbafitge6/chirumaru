import { createUser, getUserByEmail } from '@/lib/auth';

export async function POST(request: Request) {
  try {
    const { email, password, loginMethod } = await request.json();

    if (!email || !password) {
      return Response.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    const existingUser = await getUserByEmail(email);
    if (existingUser) {
      return Response.json(
        { error: 'User already exists' },
        { status: 400 }
      );
    }

    const user = await createUser(email, password, loginMethod || 'Email');

    return Response.json({
      message: 'User created successfully',
      userId: user.id,
    });
  } catch (error) {
    console.error('Signup error:', error);
    return Response.json(
      { error: 'Failed to create user' },
      { status: 500 }
    );
  }
}
