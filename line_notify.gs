const SCRIPT_PROPERTIES = {
  LINE_TOKEN_KEY: 'LINE_MESSAGING_API_TOKEN',
  LINE_ID_KEY: 'LINE_GROUP_ID'
};

/**
 * Googleフォーム送信時に実行されるメインの関数
 * @param {Object} e イベントオブジェクト
 */
function onFormSubmit(e) {
  try {
    const formResponse = e.namedValues;
    if (!formResponse) {
      Logger.log('フォームの回答データが取得できませんでした。');
      return;
    }

    const headers = SpreadsheetApp.getActiveSheet().getRange(1, 1, 1, SpreadsheetApp.getActiveSheet().getLastColumn()).getValues()[0];
    const messageParts = headers.map(header => {
      const answer = formResponse[header] ? formResponse[header][0] : '(未回答)';
      return `■${header}\n${answer}`;
    });

    const messageToSend = messageParts.join('\n\n');

    Logger.log("送信メッセージ:\n" + messageToSend);

    sendLinePushMessage(messageToSend);

  } catch (error) {
    Logger.log(`エラーが発生しました: ${error.message}\nスタックトレース: ${error.stack}`);
  }
}

/**
 * LINE Messaging APIにプッシュメッセージを送信する関数
 * @param {string} textMessage 送信するテキストメッセージ
 */
function sendLinePushMessage(textMessage) {
  const properties = PropertiesService.getScriptProperties();
  const channelAccessToken = properties.getProperty(SCRIPT_PROPERTIES.LINE_TOKEN_KEY);
  const groupId = properties.getProperty(SCRIPT_PROPERTIES.LINE_ID_KEY);

  if (!channelAccessToken || !groupId) {
    Logger.log('チャネルアクセストークンまたはグループIDがスクリプトプロパティに設定されていません。');
    return;
  }

  const lineApiUrl = 'https://api.line.me/v2/bot/message/push';

  const payload = {
    'to': groupId,
    'messages': [{
      'type': 'text',
      'text': textMessage,
    }],
  };

  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': {
      'Authorization': `Bearer ${channelAccessToken}`,
    },
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true,
  };

  const response = UrlFetchApp.fetch(lineApiUrl, options);
  const responseCode = response.getResponseCode();
  const responseBody = response.getContentText();

  Logger.log(`LINE API Response Code: ${responseCode}`);
  Logger.log(`LINE API Response Body: ${responseBody}`);
}