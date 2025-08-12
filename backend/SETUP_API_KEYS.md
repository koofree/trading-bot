# Setting Up Upbit API Keys

## How to Get Your Upbit API Keys

1. **Log in to Upbit**: Go to https://upbit.com and log in to your account

2. **Navigate to API Management**:
   - Click on your profile icon
   - Go to "Open API Management" or "API 관리"

3. **Create New API Key**:
   - Click "Create API Key" or "API Key 생성"
   - Set a name for your API key
   - Select permissions (for trading bot, you need):
     - Account inquiry (계좌 조회)
     - Order inquiry (주문 조회)
     - Order placement (주문하기) - if you want to trade
   - Set IP whitelist if required

4. **Save Your Keys**:
   - **Access Key**: This is your public API key
   - **Secret Key**: This is your private key (shown only once!)
   - Save both keys securely

## Add Keys to Your Environment

1. Open the `.env` file in the backend directory:
   ```
   /Users/fig/Works/prototyping/trading-bot/backend/.env
   ```

2. Replace the placeholder values with your actual keys:
   ```
   UPBIT_ACCESS_KEY=your_actual_access_key_here
   UPBIT_SECRET_KEY=your_actual_secret_key_here
   ```

   Example format (these are not real keys):
   ```
   UPBIT_ACCESS_KEY=x8NklZqG3xKNvZx5HNxZqG3xK
   UPBIT_SECRET_KEY=ZqG3xKNvZx5HNx8NklZqG3xKNv
   ```

## Test Your Configuration

Run the test script to verify your keys work:
```bash
cd /Users/fig/Works/prototyping/trading-bot/backend
python test_upbit_auth.py
```

If successful, you should see:
- ✅ Authentication successful!
- List of your account balances

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit your `.env` file to version control
- Never share your secret key with anyone
- Consider using read-only API keys for testing
- Use IP whitelist for production environments

## Troubleshooting

### "invalid_access_key" Error
- Double-check that you copied the entire access key
- Ensure there are no extra spaces or quotes
- Verify the key hasn't expired or been deleted

### "jwt_verification_error" Error
- The secret key is incorrect
- Make sure you copied the complete secret key
- Check that the secret key matches the access key pair

### Connection Issues
- Check if Upbit API is accessible from your location
- Verify your internet connection
- Check if your IP is whitelisted (if IP restriction is enabled)