import AdminLogin from '../../components/security/AdminLogin';

// App Router pages receive route props, while the shared login component also
// accepts an optional link for the public site's embedded entry point.
export default function LoginPage() {
  return <AdminLogin />;
}
