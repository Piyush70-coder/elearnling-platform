from django.core.management.base import BaseCommand
from compiler.models import CodeTemplate

class Command(BaseCommand):
    help = 'Creates default code templates for supported programming languages'

    def handle(self, *args, **options):
        templates = [
            {
                'language': 'c',
                'template_code': '#include <stdio.h>\n\nint main() {\n    // Your code here\n    printf("Hello, World!\\n");\n    return 0;\n}',
                'description': 'C language template with stdio.h included'
            },
            {
                'language': 'cpp',
                'template_code': '#include <iostream>\nusing namespace std;\n\nint main() {\n    // Your code here\n    cout << "Hello, World!" << endl;\n    return 0;\n}',
                'description': 'C++ template with iostream and standard namespace'
            },
            {
                'language': 'java',
                'template_code': 'public class Main {\n    public static void main(String[] args) {\n        // Your code here\n        System.out.println("Hello, World!");\n    }\n}',
                'description': 'Java template with Main class and main method'
            },
            {
                'language': 'python',
                'template_code': '# Python code\n\ndef main():\n    # Your code here\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()',
                'description': 'Python template with main function'
            },
            {
                'language': 'javascript',
                'template_code': '// JavaScript code\n\nfunction main() {\n    // Your code here\n    console.log("Hello, World!");\n}\n\nmain();',
                'description': 'JavaScript template with main function'
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template, created = CodeTemplate.objects.update_or_create(
                language=template_data['language'],
                defaults={
                    'template_code': template_data['template_code'],
                    'description': template_data['description']
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} and updated {updated_count} code templates'
            )
        )