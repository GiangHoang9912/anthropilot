class Message:
  def __init__(self):
    self.short_description = """Dựa vào dữ kiện. Hãy tóm tắt lại nội dung chính của tài liệu trong Khoảng 10-20 từ"""
    self.summary = """Dựa vào dữ kiện. Hãy tóm tắt lại nội dung chính của tài liệu và lấy 3 câu hỏi phải liên quan đến toàn bộ nội dung của tài liệu, để làm rõ nội dung của tài liệu. Trả về không thêm bớt không giải thích chỉ bao gồm json có format như sau: {"summary": "nội dung tóm tắt", "questions": ["câu hỏi 1", "câu hỏi 2", "câu hỏi 3"]}"""
    self.template = """system: Bạn là GoAI, Được Tạo ra bởi GoAI. \nSử dụng thông tin sau đây để trả lời câu hỏi, đối với các dạng bài tập thì sử dụng chính xác dữ kiện trong bài tập gần nhất không thêm bớt để tránh thừa thiếu dữ liệu. Nếu bạn không biết câu trả lời, hãy nói không biết, đừng cố tạo ra câu trả lời\n{context}\n
      user: \n{question}\n
      assistant: \n"""

  def get_message(self, type, history=None):
    if type == "summary":
      return self.summary
    elif type == "short_description":
      return self.short_description
    elif type == "template":
      return self.template
    elif type == "template_history":
      if history is None:
        return self.template
      else:
        history_template = self.template
        for i in range(len(history)):
            history_template += f"user: \n{history[i]['user']}\n"
            history_template += f"assistant: \n{history[i]['assistant']}\n"
        history_template += "user: \n{question}\n"
        history_template += "assistant: \n"
        return history_template

    else:
      return None