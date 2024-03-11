export default function PublicRoutes() {
    return (
        <Routes>
          <Route path="/:modified_message_name" element={<RootRoute />} />
        </Routes>
    );
  }
}
