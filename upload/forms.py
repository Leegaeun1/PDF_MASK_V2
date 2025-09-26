from django import forms

class PDFUploadForm(forms.Form):
    file = forms.FileField(
        label='PDF 선택',
        help_text='최대 10MB, PDF만 업로드 가능!',
        widget=forms.ClearableFileInput(attrs={'accept': 'application/pdf'}) # 파일 선택 할수있음. 업로드 된 경우에는 취소할수도있음.
        # pdf파일만 보이도록 필터링!
    )

    def clean_file(self): # 유효성 검증. 사용자가 파일 제출하면 실행됨. 장고는 clean_필드이름 형식의 메서드를 자동으로 호출하여 해당 필드의 데이터가 올바른지 검사함
        f = self.cleaned_data['file'] # 업로드한 파일 객체
        if f.content_type not in ('application/pdf', 'application/x-pdf'): # pdf에서 다른 종류의 파일로 변경했을때 걸러내줌.
            raise forms.ValidationError('PDF 파일만 업로드할 수 있습니다.')
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError('파일 용량은 10MB 이하여야 합니다.')
        # 간단 확장자 체크(추가 검증)
        if not f.name.lower().endswith('.pdf'):
            raise forms.ValidationError('파일 확장자가 .pdf 이어야 합니다.')
        return f
