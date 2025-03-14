import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/common/card";
import { CircleAlert, ClipboardIcon } from "lucide-react";
import { Button } from "../ui/common/button";
import { useTranslations } from "next-intl";

export default function Auth () {
    const t = useTranslations("Auth");

    return (
        <Card className="m-4 items-center text-center flex-col font-bold">
            <CardHeader>
                <CardTitle>{t("title")}</CardTitle>
            </CardHeader>
            <CardContent>
                <CircleAlert className="w-full" size={128}/>
            </CardContent>
            <CardFooter className="flex-col space-y-2">
                <p>{t("authorize")}</p>
                <Button className='w-full rounded-xl shadow-none text-center m-2'>
                    {process.env.NEXT_PUBLIC_BOT_URL} <ClipboardIcon />
                </Button>
            </CardFooter>
        </Card>
    )
  };