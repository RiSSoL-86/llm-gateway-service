# llm-gateway-service

## Local run

1. Copy `src/.env.example` to `src/.env` and fill in:
   - `SECRET_KEY`: any long random string;
   - `OPENROUTER_API_KEY`: the real OpenRouter key;
   - `GATEWAY_KEYS`: our key for the endpoint, `sk-gw-...=name`.
2. Run:

   ```shell
   make install
   make db
   make migrate
   make run
   ```

3. Check:

   ```shell
   curl -N http://localhost:8000/api/v1/chat/completions \
     -H "Authorization: Bearer <key from GATEWAY_KEYS>" \
     -H "Content-Type: application/json" \
     -d '{"model": "openai/gpt-4o-mini", "stream": true,
          "messages": [{"role": "user", "content": "Hi"}]}'
   ```

- Swagger: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/, create a user with `make superuser`.
