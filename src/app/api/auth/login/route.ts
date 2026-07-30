import { getUserByEmail, verifyPassword } from '@/lib/auth';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return Response.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    const user = await getUserByEmail(email);
    if (!user) {
      return Response.json(
        { error: 'User not found' },
        { status: 401 }
      );
    }

    const passwordValid = await verifyPassword(
      password,
      user.fields.Password
    );

    if (!passwordValid) {
      return Response.json(
        { error: 'Invalid password' },
        { status: 401 }
      );
    }

    return Response.json({
      message: 'Login successful',
      userId: user.id,
      email: user.fields.Email,
    });
  } catch (error) {
    console.error('Login error:', error);
    return Response.json(
      { error: 'Failed to login' },
      { status: 500 }
    );
  }
}
